# utility_functions.py

import challonge
from .models import Person, Matchup
# import pandas
import os
from django.db.models import Q, Sum


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


# update everyone's scores based on if they are an attendee or not
def update_all_scores(sn):
    attendees = Person.objects.filter(attendee__sn=sn).distinct()
    non_attendee_scorers = Person.objects.exclude(pk__in=attendees).filter(Q(p1_match_set__sn=sn) | Q(p2_match_set__sn=sn)).distinct()
    for c_person in attendees:
        c_person.score = c_person.attendee_set.get(sn=sn).end_score
        c_person.save()
    for c_person in non_attendee_scorers:
        c_person.score = (
            c_person.score
            + c_person.p1_match_set.filter(sn=sn).aggregate(Sum('p1_score_change', default=0))['p1_score_change__sum']
            + c_person.p2_match_set.filter(sn=sn).aggregate(Sum('p2_score_change', default=0))['p2_score_change__sum']
        )
        c_person.save()
    return


# function to help update additional matches
def add_additional_matchup(c_p1, c_p2, px_wins, py_wins):
    people = Person.objects
    c_px = people.get_person(c_p1)
    c_py = people.get_person(c_p2)
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
# def add_all_additional_matchups(path_to_file):
#     df = pandas.read_csv(path_to_file, index_col=0)
#     items_to_add = []
#     for i, j in df.iterrows():
#         for k, l in j.iteritems():
#             if not pandas.isnull(l):
#                 vals = str(l).replace(" ", "").split(":")
#                 items_to_add.append([i, k, int(vals[0]), int(vals[1])])
#     for item in items_to_add:
#         add_additional_matchup(item[0], item[1], item[2], item[3])


def reset_scores(max_val=200.0, min_val=60.0, interval=10.0):
    """Resets scores starting with the highest score as max_val,
    and decrementing by interval for each rank"""
    for person in Person.objects.filter(tag=Person.MEMBER):
        person.score = max(max_val - ((person.rank or 100) - 1) * interval, min_val)
        person.save()
