# Generated by Django 5.0.2 on 2024-07-03 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_work_series_num'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='embed_in_homepage',
            field=models.BooleanField(default=False),
        ),
    ]