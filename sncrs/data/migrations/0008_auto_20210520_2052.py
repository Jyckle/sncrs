# Generated by Django 3.2.3 on 2021-05-20 20:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0007_auto_20210520_2050'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attendee',
            old_name='person_id',
            new_name='person',
        ),
        migrations.RenameField(
            model_name='attendee',
            old_name='sn_id',
            new_name='sn',
        ),
    ]
