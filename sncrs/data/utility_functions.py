# utility_functions.py

import challonge
from .models import Person, Matchup
import pandas
import os


# given a tournament, get the bracket participants associated with this url
def get_challonge_bracket_data(bracket):
    # Set up credentials to access challonge account
    challonge.set_credentials(os.environ.get('CHALLONGE_USER'), os.environ.get('CHALLONGE_KEY'))
    # get the challonge tournament
    tournament = challonge.tournaments.show(bracket.url.replace("https://challonge.com/", ""))
    # get all participants from challonge
    participants = challonge.participants.index(tournament["id"])
    # get all matches from challonge
    matches = challonge.matches.index(tournament["id"])

    return participants, matches


# given a participant name, check for them in SNCRS
def get_sncrs_person(text):
    for person in Person.objects.all():
        if person.display_name.lower() == text.lower():
            return person
        for alias in person.alias_set.all():
            if alias.name.lower() == text.lower():
                return person
    return None


# score change calculation for P1 in a set vs P2
def get_score_change(p1_score, p2_score, p1_wins, p2_wins):
    points = 0
    if int(p1_wins) == -1 or int(p2_wins) == -1:
        return points
    elif p1_wins > p2_wins:
        points = 5 * (1 - 1 / (1 + 5.0 ** ((float(p2_score) - float(p1_score)) / 80)))
    else:
        points = -3 * (1 / (1 + 10.0 ** ((float(p2_score) - float(p1_score)) / 80)))
    return points


# calculate ranks given scores
def assign_score_based_ranks(person_list):
    sorted_list = sorted(person_list, key=lambda current_person: -current_person.score)
    c_rank = 1
    prev_score = 0
    people_to_add = []
    for person in sorted_list:
        if person.score != prev_score:
            if len(people_to_add) != 0:
                for add_person in people_to_add:
                    add_person.rank = c_rank
                    add_person.save()
                c_rank += len(people_to_add)
                people_to_add = []
            prev_score = person.score
        people_to_add.append(person)
    for add_person in people_to_add:
        add_person.rank = c_rank
        add_person.save()
    return


# placement score change calculations
def get_placement_score_change(attendee, sn_headcount):
    points = 5.0 if attendee.person.status == Person.ELITE else 0.0
    if attendee.start_seed >= attendee.end_seed:
        points += (attendee.start_seed - attendee.end_seed + 0.5) * 30 / sn_headcount + 3
    return points


# update everyone's scores based on if they are an attendee or not
def update_all_scores(sn):
    people = Person.objects.filter(tag=Person.MEMBER)
    for c_person in people:
        try:
            attendee = sn.attendee_set.get(person=c_person)
        except Exception:
            attendee = None

        if attendee is not None:
            c_person.score = attendee.end_score
            c_person.save()
    return


# function to help update additional matches
def add_additional_matchup(c_p1, c_p2, px_wins, py_wins):
    c_px = get_sncrs_person(c_p1)
    c_py = get_sncrs_person(c_p2)
    try:
        matchup = Matchup.objects.get(px=c_px, py=c_py)
    except Exception:
        matchup = None

    if matchup is not None:
        print("Not found")
        return
    else:
        matchup.px_additional_wins = px_wins
        matchup.py_additional_wins = py_wins
        matchup.save()
    return


# function to add all additional matches from csv
def add_all_additional_matchups(path_to_file):
    df = pandas.read_csv(path_to_file, index_col=0)
    items_to_add = []
    for i, j in df.iterrows():
        for k, l in j.iteritems():
            if not pandas.isnull(l):
                vals = str(l).replace(" ", "").split(":")
                items_to_add.append([i, k, int(vals[0]), int(vals[1])])
    for item in items_to_add:
        add_additional_matchup(item[0], item[1], item[2], item[3])


def reset_scores(max_val=200.0, min_val=60.0, interval=10.0):
    """Resets scores starting with the highest score as max_val,
    and decrementing by interval for each rank"""
    for person in Person.objects.filter(tag=Person.MEMBER):
        person.score = max(max_val - ((person.rank or 100) - 1) * interval, min_val)
        person.save()
