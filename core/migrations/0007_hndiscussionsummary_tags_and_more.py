# Generated by Django 5.2.1 on 2025-05-13 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_hndiscussionsummary_description_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='hndiscussionsummary',
            name='tags',
            field=models.TextField(blank=True, help_text='Tags for the blog post'),
        ),
        migrations.AlterField(
            model_name='hndiscussionsummary',
            name='description',
            field=models.TextField(blank=True, help_text='Description of the blog post'),
        ),
    ]
