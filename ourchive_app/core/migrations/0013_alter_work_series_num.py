# Generated by Django 5.0.6 on 2024-06-28 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_alter_adminannouncement_created_on_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='work',
            name='series_num',
            field=models.IntegerField(default=1),
        ),
    ]
