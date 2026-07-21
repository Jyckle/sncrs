# sn_calculate.py

from .utility_functions import update_all_scores
from .snapshot_logic import store_previous_snapshot_or_current_scores
from .models import GameTitle, Matchup, Medal, Person


def set_challonge_data(sn):
    # Create all the matches for this smashNight
    for bracket in sn.bracket_set.all():
        bracket.create_matches()
    # update any added challenge matches
    sn.update_all_challenge_matches()
    # Create all the bracket rankings for this smashNight
    for bracket in sn.bracket_set.all():
        bracket.create_bracket_ranks()


def set_sncrs_data(sn):
    # create or update the matchup table and medal counts for each game title played this night
    for game_title in GameTitle.objects.filter(bracket__sn=sn).distinct():
        # Limit calculations to attendees
        attendees = Person.objects.filter(
            placement__bracket__sn=sn, placement__bracket__game_title=game_title
        ).distinct()
        Matchup.objects.create_or_update_matchups_table(game_title=game_title)
        Medal.objects.create_or_update_medal_counts(game_title=game_title, person_list=attendees)
    # Create all the attendee rankings for this smashNight and record initial scores
    sn.create_all_attendee_ranks()
    # update attendee scores
    sn.update_attendee_scores()
    # update everyone's scores
    update_all_scores(sn)


def full_update(sn):

    # Store current scores as Snapshot for each person
    store_previous_snapshot_or_current_scores(sn, "start")

    # create matches and brackets with challonge data
    set_challonge_data(sn)

    # create attendee rankings, scores, and update everyone's scores
    set_sncrs_data(sn)

    # Store the updated scores as Snapshot for each person
    store_previous_snapshot_or_current_scores(sn, "end")
