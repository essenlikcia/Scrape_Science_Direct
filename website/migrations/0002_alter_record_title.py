# Generated by Django 5.0.3 on 2024-04-25 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='title',
            field=models.CharField(max_length=500),
        ),
    ]
