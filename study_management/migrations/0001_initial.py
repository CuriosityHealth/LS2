# Generated by Django 2.0.1 on 2018-01-06 04:44

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Datapoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(editable=False, unique=True)),
                ('created_date_time', models.DateTimeField(auto_now_add=True)),
                ('schema_namespace', models.CharField(max_length=64)),
                ('schema_name', models.CharField(max_length=32)),
                ('schema_version_major', models.PositiveSmallIntegerField()),
                ('schema_version_minor', models.PositiveSmallIntegerField()),
                ('schema_version_patch', models.PositiveSmallIntegerField()),
                ('ap_source_name', models.CharField(max_length=64)),
                ('ap_source_creation_date_time', models.DateTimeField()),
                ('ap_source_modality', models.CharField(max_length=32)),
                ('body', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='LoginTimeout',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('disable_until', models.DateTimeField()),
                ('username', models.CharField(blank=True, max_length=255, null=True)),
                ('remote_ip', models.CharField(db_index=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('label', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='PasswordChangeEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('encoded_password', models.CharField(max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Researcher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Study',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='researcher',
            name='studies',
            field=models.ManyToManyField(blank=True, to='study_management.Study'),
        ),
        migrations.AddField(
            model_name='researcher',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='participant',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='study_management.Study'),
        ),
        migrations.AddField(
            model_name='participant',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='datapoint',
            name='participant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='study_management.Participant'),
        ),
        migrations.AddField(
            model_name='datapoint',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='study_management.Study'),
        ),
    ]
