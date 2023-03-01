# sn_calculate.py

from .utility_functions import update_all_scores
from .match_logic import create_all_matches, update_all_challenge_matches
from .bracket_logic import create_all_bracket_ranks
from .attendee_logic import create_all_attendee_ranks, update_attendee_scores
from .matchup_logic import create_matchup_table
from .snapshot_logic import store_scores
from .opponent_logic import set_all_rivals, set_all_demons


def set_challonge_data(sn):
    # Create all the matches for this smashNight
    create_all_matches(sn)
    # update any added challenge matches
    update_all_challenge_matches(sn)
    # Create all the bracket rankings for this smashNight
    create_all_bracket_ranks(sn)


def set_sncrs_data(sn):
    # create or update the matchup table
    create_matchup_table()
    # Create all the attendee rankings for this smashNight and record initial scores
    create_all_attendee_ranks(sn)
    # update attendee scores
    update_attendee_scores(sn)
    # if the code has not already run
    if not sn.automations_ran:
        # update everyone's scores
        update_all_scores(sn)


def full_update(sn):

    # Store current scores as Snapshot for each person
    store_scores(sn, "start")

    # create matches and brackets with challonge data
    set_challonge_data(sn)

    # create attendee rankings, scores, and update everyone's scores
    set_sncrs_data(sn)

    if not sn.automations_ran:
        # Store the updated scores as Snapshot for each person
        store_scores(sn, "end")
        sn.automations_ran = True
        sn.save()

    # set everyone's rivals as calculated by the new data
    set_all_rivals()

    # set everyone's demon as calculated by the new data
    set_all_demons()
