# Generated by Django 3.2.3 on 2021-05-20 16:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0005_auto_20210520_1655'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='alias',
            options={'verbose_name_plural': 'aliases'},
        ),
        migrations.AlterModelOptions(
            name='match',
            options={'verbose_name_plural': 'matches'},
        ),
        migrations.AlterModelOptions(
            name='person',
            options={'verbose_name_plural': 'people'},
        ),
        migrations.AlterModelOptions(
            name='smashnight',
            options={'verbose_name_plural': 'smashnights'},
        ),
    ]
