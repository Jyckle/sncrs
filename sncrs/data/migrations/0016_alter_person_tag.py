# Generated by Django 3.2.3 on 2021-05-22 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0015_auto_20210520_2145'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='tag',
            field=models.IntegerField(blank=True, choices=[(0, 'Member'), (1, 'Guest')], null=True),
        ),
    ]
