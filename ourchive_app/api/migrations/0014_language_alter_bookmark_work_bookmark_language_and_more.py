# Generated by Django 5.0.2 on 2024-05-04 16:27

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_add_auto_allow_upload'),
    ]

    operations = [
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('display_name', models.CharField(max_length=200)),
                ('ietf_code', models.CharField(max_length=40)),
            ],
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='work',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.work'),
        ),
        migrations.AddField(
            model_name='user',
            name='default_languages',
            field=models.ManyToManyField(related_name='users', to='api.language'),
        ),
        migrations.AddField(
            model_name='bookmark',
            name='languages',
            field=models.ManyToManyField(to='api.language'),
        ),
        migrations.AddField(
            model_name='bookmarkcollection',
            name='languages',
            field=models.ManyToManyField(to='api.language'),
        ),
        migrations.AddField(
            model_name='work',
            name='languages',
            field=models.ManyToManyField(to='api.language'),
        ),
    ]