# Generated by Django 4.2.3 on 2023-09-15 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0061_alter_cliptag_tag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cliptag',
            name='clips',
        ),
        migrations.AddField(
            model_name='clip',
            name='tags',
            field=models.ManyToManyField(related_name='clips', to='data.cliptag'),
        ),
    ]