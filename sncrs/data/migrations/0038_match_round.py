# Generated by Django 3.2.3 on 2021-05-29 02:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0037_alter_person_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='round',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
