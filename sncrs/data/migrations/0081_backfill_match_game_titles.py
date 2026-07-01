from django.db import migrations


def backfill_match_game_titles(apps, schema_editor):
    Match = apps.get_model('data', 'Match')
    GameTitle = apps.get_model('data', 'GameTitle')
    for game_title in GameTitle.objects.all():
        Match.objects.filter(bracket__game_title=game_title).update(game_title=game_title)


def reverse_backfill(apps, schema_editor):
    Match = apps.get_model('data', 'Match')
    GameTitle = apps.get_model('data', 'GameTitle')
    default, _ = GameTitle.objects.get_or_create(name='SSBU')
    Match.objects.all().update(game_title=default)


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0080_matchup_unique_per_game'),
    ]

    operations = [
        migrations.RunPython(backfill_match_game_titles, reverse_code=reverse_backfill),
    ]
