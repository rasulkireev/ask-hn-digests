from django.test import TestCase

from core.models import HNDiscussionSummary, Tag, TagAlias, TopicLane


class TagNormalizationTests(TestCase):
    def make_summary(self, discussion_id, title):
        return HNDiscussionSummary.objects.create(
            discussion_id=discussion_id,
            discussion_title=title,
            comment_ids=[],
            short_summary="Short summary",
            slug=f"summary-{discussion_id}",
            title=title,
            description="Description",
            long_summary="Long summary",
        )

    def test_aliases_collapse_to_canonical_tags(self):
        tags = Tag.objects_from_raw_tags("AI, artificial intelligence, ML, Hacker News")

        self.assertEqual([tag.name for tag in tags], ["AI", "Machine Learning"])
        self.assertEqual(Tag.objects.filter(slug__in=["ai", "machine-learning"]).count(), 2)
        self.assertEqual(TagAlias.objects.get(slug="artificial-intelligence").tag.name, "AI")
        self.assertFalse(Tag.objects.filter(slug="hacker-news").exists())

    def test_c_and_c_plus_plus_remain_distinct_despite_slug_collision(self):
        tags = Tag.objects_from_raw_tags("C, C++, cpp")

        self.assertEqual([tag.name for tag in tags], ["C", "C++"])
        self.assertEqual(Tag.objects.get(slug="c").name, "C")
        self.assertEqual(Tag.objects.get(slug="c-plus-plus").name, "C++")
        self.assertEqual(TagAlias.objects.get(slug="cpp").tag.name, "C++")

    def test_legacy_tag_fallback_keeps_c_and_c_plus_plus_distinct(self):
        summary = self.make_summary(1, "Legacy C summary")
        summary.legacy_tags = "C, C++"
        summary.save(update_fields=["legacy_tags"])

        self.assertEqual(summary.get_tags_list(), ["C", "C++"])

    def test_summary_tag_lookup_is_exact(self):
        ai_summary = self.make_summary(1, "AI summary")
        ai_summary.set_tags_from_text("AI")

        airtable_summary = self.make_summary(2, "Airtable summary")
        airtable_summary.set_tags_from_text("Airtable")

        summaries = list(HNDiscussionSummary.get_summaries_by_tag("ai"))

        self.assertEqual(summaries, [ai_summary])
        self.assertNotIn(airtable_summary, summaries)

    def test_get_tags_list_uses_prefetched_tags(self):
        summary = self.make_summary(1, "Prefetched summary")
        summary.set_tags_from_text("TypeScript, AI")

        prefetched_summary = HNDiscussionSummary.objects.prefetch_related("tags").get(pk=summary.pk)

        with self.assertNumQueries(0):
            self.assertEqual(prefetched_summary.get_tags_list(), ["AI", "TypeScript"])

    def test_tag_counts_are_database_annotations(self):
        first_summary = self.make_summary(1, "First")
        first_summary.set_tags_from_text("Postgres, Databases")
        second_summary = self.make_summary(2, "Second")
        second_summary.set_tags_from_text("PostgreSQL")

        postgres = Tag.objects.visible().get(slug="postgresql")
        databases = Tag.objects.visible().get(slug="databases")

        self.assertEqual(postgres.summary_count, 2)
        self.assertEqual(databases.summary_count, 1)
        self.assertEqual(postgres.topic_lane, TopicLane.DEVTOOLS_INFRA)

    def test_direct_tag_create_infers_slug_and_topic_lane(self):
        tag = Tag.objects.create(name="Kubernetes")

        self.assertEqual(tag.slug, "kubernetes")
        self.assertEqual(tag.topic_lane, TopicLane.DEVTOOLS_INFRA)

    def test_punctuation_canonical_tags_infer_topic_lanes(self):
        tags = Tag.objects_from_raw_tags("Node.js, CI/CD")

        self.assertEqual([tag.name for tag in tags], ["Node.js", "CI/CD"])
        self.assertEqual(Tag.objects.get(slug="nodejs").topic_lane, TopicLane.PROGRAMMING)
        self.assertEqual(Tag.objects.get(slug="cicd").topic_lane, TopicLane.DEVTOOLS_INFRA)
