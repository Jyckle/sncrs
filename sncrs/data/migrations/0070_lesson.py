# Generated by Django 5.0.1 on 2024-08-16 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0069_rename_link_sociallink_url_alter_site_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(blank=True, null=True)),
                ('text', models.TextField()),
            ],
        ),
    ]
