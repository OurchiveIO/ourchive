# Generated by Django 4.2.4 on 2024-01-31 02:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_user_chive_export_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='filterable',
            field=models.BooleanField(default=True),
        ),
    ]