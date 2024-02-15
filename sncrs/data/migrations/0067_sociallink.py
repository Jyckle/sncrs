# Generated by Django 4.2.4 on 2023-08-23 00:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0066_quotetag_quotespeaker_quote'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site', models.CharField(max_length=50)),
                ('link', models.URLField(blank=True, null=True)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='socials', to='data.person')),
            ],
        ),
    ]
