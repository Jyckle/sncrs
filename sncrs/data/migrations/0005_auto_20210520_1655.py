# Generated by Django 3.2.3 on 2021-05-20 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0004_auto_20210520_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='bracket_demon',
            field=models.ManyToManyField(blank=True, related_name='_data_person_bracket_demon_+', to='data.Person'),
        ),
        migrations.AlterField(
            model_name='person',
            name='mains',
            field=models.ManyToManyField(blank=True, to='data.Character'),
        ),
        migrations.AlterField(
            model_name='person',
            name='rivals',
            field=models.ManyToManyField(blank=True, related_name='_data_person_rivals_+', to='data.Person'),
        ),
    ]
