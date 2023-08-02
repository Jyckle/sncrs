from django.db import migrations

def migrate_mains(apps, schema_editor):
    Person = apps.get_model("data", "Person")
    Character = apps.get_model("data", "Character")
    for person in Person.objects.all():
        for ind, current_main in enumerate([person.main_1, person.main_2, person.main_3]):
            if current_main:
                character = Character.objects.get(id=current_main.id)
                person.main_set.create(character=character, order=ind)

class Migration(migrations.Migration):

    dependencies = [
        ('data', '0053_add_preferred_character'),
    ]

    operations = [
        migrations.RunPython(migrate_mains),
    ]
