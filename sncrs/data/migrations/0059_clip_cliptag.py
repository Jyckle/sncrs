# Generated by Django 4.2.4 on 2023-08-14 23:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0058_remove_person_chat_tag'),
    ]

    operations = [
        migrations.CreateModel(
            name='Clip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(blank=True, null=True)),
                ('title', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='ClipTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(max_length=50)),
                ('clip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='data.clip')),
            ],
        ),
    ]
