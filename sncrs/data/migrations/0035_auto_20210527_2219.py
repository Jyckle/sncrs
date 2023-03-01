# Generated by Django 3.2.3 on 2021-05-27 22:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0034_alter_personsnapshot_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='bracket',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='data.bracket'),
        ),
        migrations.AddField(
            model_name='match',
            name='challonge_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
