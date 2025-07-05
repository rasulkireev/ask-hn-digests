import pytest
from django.urls import reverse
from django.test import Client
from core.models import HNDiscussionSummary


@pytest.mark.django_db
class TestSearchView:
    def test_search_view_loads(self):
        """Test that the search view loads successfully."""
        client = Client()
        url = reverse("search")
        response = client.get(url)
        assert response.status_code == 200
        assert "Search Results" in response.content.decode()

    def test_search_with_query(self):
        """Test search functionality with a query."""
        # Create a test discussion summary
        HNDiscussionSummary.objects.create(
            discussion_id=123456,
            discussion_title="Test Discussion",
            title="Test Title",
            short_summary="This is a test summary",
            long_summary="This is a longer test summary with more details",
            description="Test description",
            slug="test-title",
            comment_ids=[1, 2, 3],
            tags="test,search,python"
        )
        
        client = Client()
        url = reverse("search")
        response = client.get(url, {'q': 'test'})
        
        assert response.status_code == 200
        assert "Test Title" in response.content.decode()
        assert "Found 1 result" in response.content.decode()

    def test_search_no_results(self):
        """Test search with no matching results."""
        client = Client()
        url = reverse("search")
        response = client.get(url, {'q': 'nonexistent'})
        
        assert response.status_code == 200
        assert "No results found" in response.content.decode()

    def test_search_empty_query(self):
        """Test search with empty query."""
        client = Client()
        url = reverse("search")
        response = client.get(url, {'q': ''})
        
        assert response.status_code == 200
        assert "Enter a search term" in response.content.decode()