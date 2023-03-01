# Generated by Django 3.2.3 on 2021-05-25 20:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0020_auto_20210525_1934'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='bracket_demon',
        ),
        migrations.AddField(
            model_name='person',
            name='bracket_demon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='data.person'),
        ),
    ]
