# Generated by Django 5.0.3 on 2024-05-04 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_record_pii'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='orcid_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
