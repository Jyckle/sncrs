from django.db import migrations


def backfill_challenge_match_game_titles(apps, schema_editor):
    Match = apps.get_model('data', 'Match')
    GameTitle = apps.get_model('data', 'GameTitle')
    roa2 = GameTitle.objects.get(name='RoA2')
    # CHALLENGE = 1; all challenge matches with id > 897 are RoA2
    Match.objects.filter(type=1, id__gt=897).update(game_title=roa2)


def reverse_backfill(apps, schema_editor):
    Match = apps.get_model('data', 'Match')
    GameTitle = apps.get_model('data', 'GameTitle')
    ssbu, _ = GameTitle.objects.get_or_create(name='SSBU')
    Match.objects.filter(type=1, id__gt=897).update(game_title=ssbu)


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0081_backfill_match_game_titles'),
    ]

    operations = [
        migrations.RunPython(backfill_challenge_match_game_titles, reverse_code=reverse_backfill),
    ]
