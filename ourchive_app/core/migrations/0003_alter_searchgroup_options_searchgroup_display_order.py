# Generated by Django 5.0.2 on 2024-06-12 03:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_searchgroup_searchgroup_unique_label_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='searchgroup',
            options={'ordering': ['display_order', 'label']},
        ),
        migrations.AddField(
            model_name='searchgroup',
            name='display_order',
            field=models.IntegerField(default=1),
        ),
    ]
