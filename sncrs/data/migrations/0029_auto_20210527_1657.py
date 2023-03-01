# Generated by Django 3.2.3 on 2021-05-27 16:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0028_alter_personsnapshot_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personsnapshot',
            name='person',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='data.person'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='personsnapshot',
            name='sn',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='data.smashnight'),
            preserve_default=False,
        ),
    ]
