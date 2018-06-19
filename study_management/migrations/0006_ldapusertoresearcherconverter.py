# Generated by Django 2.0.6 on 2018-06-13 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('study_management', '0005_participantaccountgenerationrequestevent_participantaccountgenerationtimeout'),
    ]

    operations = [
        migrations.CreateModel(
            name='LDAPUserToResearcherConverter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ldap_username', models.CharField(max_length=50)),
                ('converted', models.BooleanField(default=False)),
                ('studies', models.ManyToManyField(blank=True, to='study_management.Study')),
            ],
        ),
    ]