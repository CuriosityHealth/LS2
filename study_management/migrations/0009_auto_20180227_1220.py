# Generated by Django 2.0.1 on 2018-02-27 17:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('study_management', '0008_auto_20180226_2252'),
    ]

    operations = [
        migrations.RenameField(
            model_name='studyconfiguration',
            old_name='encrypt_by_deault',
            new_name='encrypt_by_default',
        ),
    ]
