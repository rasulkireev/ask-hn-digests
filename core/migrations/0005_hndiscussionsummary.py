# Generated by Django 5.2.1 on 2025-05-13 08:10

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_newslettersubscriber_added_to_buttondown'),
    ]

    operations = [
        migrations.CreateModel(
            name='HNDiscussionSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('discussion_id', models.BigIntegerField(help_text='Hacker News discussion ID', unique=True)),
                ('comment_ids', models.JSONField(help_text='List of all comment IDs for this discussion')),
                ('date_analyzed', models.DateTimeField(auto_now_add=True, help_text='Date and time when the discussion was analyzed')),
                ('short_summary', models.TextField(help_text='Short summary of the discussion')),
                ('long_summary', models.TextField(help_text='Long summary of the discussion')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
