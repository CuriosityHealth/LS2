# Generated by Django 2.1 on 2018-10-01 01:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('study_management', '0007_auto_20180929_2340'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParticipantAuthToken',
            fields=[
                ('key', models.CharField(max_length=64, primary_key=True, serialize=False, verbose_name='Key')),
                ('last_used', models.DateTimeField(auto_now_add=True, verbose_name='Last Used')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participant_auth_token', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Participant Auth Token',
                'verbose_name_plural': 'Participant Auth Token',
            },
        ),
    ]
