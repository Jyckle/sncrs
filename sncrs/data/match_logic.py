# match_logic.py

# Match logic
# For each match obtained from challonge, assign sn, p1, p2, match and match type
# get current p1 score and current p2 scores
# record p1 wins and p2 wins
# calculate score change for each player

from .models import Match
from .utility_functions import get_challonge_bracket_data, get_sncrs_person, get_score_change
import re


# add the matches for each person
def add_matches(participant_ids, matches, c_sn, c_bracket):
    for match in matches:
        # if there is a score and two valid participants, add an element
        if "scores_csv" in match and match["scores_csv"] != "" and \
                (match["player1_id"]) in participant_ids and \
                (match["player2_id"]) in participant_ids:
            scores = re.split(r'(?<=\d)-(?=\d)|(?<=\d)-(?=-)', match["scores_csv"])
            p1_person = participant_ids[match["player1_id"]]
            p2_person = participant_ids[match["player2_id"]]
            sc1 = scores[0]
            sc2 = scores[1]
            match_id = match["id"]
            try:
                c_match = Match.objects.get(challonge_id=match_id)
            except Match.DoesNotExist:
                c_match = None
            except Match.MultipleObjectsReturned:
                print("Error: Multiple matchups found")
                continue
            if c_match is None:
                Match.objects.create(
                    p1=p1_person,
                    p2=p2_person,
                    p1_score=p1_person.score,
                    p2_score=p2_person.score,
                    p1_wins=sc1,
                    p2_wins=sc2,
                    p1_score_change=get_score_change(p1_person.score, p2_person.score, sc1, sc2),
                    p2_score_change=get_score_change(p2_person.score, p1_person.score, sc2, sc1),
                    sn=c_sn,
                    bracket=c_bracket,
                    challonge_id=match_id,
                    type=Match.BRACKET,
                    round=match["round"]
                )
            else:
                c_match.p1_wins = sc1
                c_match.p2_wins = sc2
                c_match.p1_score_change = get_score_change(c_match.p1_score, c_match.p2_score, sc1, sc2)
                c_match.p2_score_change = get_score_change(c_match.p2_score, c_match.p1_score, sc2, sc1)
                c_match.type = Match.BRACKET
                c_match.round = match["round"]
                c_match.save()
    return


# get all the challonge matches and add them
def create_all_matches(sn):
    # Loop through each bracket
    for c_bracket in sn.bracket_set.all():
        participants, matches = get_challonge_bracket_data(c_bracket)
        participant_ids = {}
        # add all participants to id list
        for participant in participants:
            sncrs_person = get_sncrs_person(participant["name"])
            if sncrs_person is not None:
                participant_ids[participant["id"]] = sncrs_person
        add_matches(participant_ids, matches, sn, c_bracket)
    return


# update a challenge match
def update_challenge_match(c_match):
    c_match.p1_score = c_match.p1.score
    c_match.p2_score = c_match.p2.score
    c_match.p1_score_change = get_score_change(c_match.p1_score, c_match.p2_score, c_match.p1_wins, c_match.p2_wins)
    c_match.p2_score_change = get_score_change(c_match.p2_score, c_match.p1_score, c_match.p2_wins, c_match.p1_wins)
    c_match.save()
    return


# update all the challenge matches
def update_all_challenge_matches(sn):
    for c_match in sn.match_set.filter(type=Match.CHALLENGE):
        update_challenge_match(c_match)
    return
