# sn_calculate.py

from .utility_functions import update_all_scores
from .matchup_logic import create_matchup_table
from .snapshot_logic import store_previous_snapshot_or_current_scores
from .opponent_logic import set_all_demons


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
    # create or update the matchup table
    create_matchup_table()
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

    # set everyone's demon as calculated by the new data
    set_all_demons()
