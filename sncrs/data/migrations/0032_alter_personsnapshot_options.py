# Generated by Django 3.2.3 on 2021-05-27 17:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0031_personsnapshot'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='personsnapshot',
            options={'ordering': ['sn__date']},
        ),
    ]
