# Generated by Django 4.2.4 on 2023-08-05 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etl', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workimport',
            name='allow_anon_comments',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='workimport',
            name='allow_comments',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='workimport',
            name='mode',
            field=models.CharField(choices=[('list', 'list'), ('single', 'single')], default='list', max_length=100),
        ),
        migrations.AddField(
            model_name='workimport',
            name='save_as_draft',
            field=models.BooleanField(default=True),
        ),
    ]