from django import template
from ..utility_functions import get_placement_score_change
from ..models import Person

register = template.Library()

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def filled_slice(value, desired_length):
    desired_length = int(desired_length)
    resulting_list = []
    for x in value:
        resulting_list.append(x)
        desired_length -= 1
    resulting_list += [None] * desired_length
    return resulting_list

@register.filter
def check_attendee_seed(c_sn, c_person):
    try:
        attendee = c_sn.attendee_set.get(person=c_person)
    except:
        attendee = None
    if attendee == None:
        return "--"
    else:
        return attendee.start_seed

@register.filter
def check_attendee_place(c_sn, c_person):
    try:
        attendee = c_sn.attendee_set.get(person=c_person)
    except:
        attendee = None
    if attendee == None:
        return "--"
    else:
        return attendee.end_seed

@register.filter
def check_attendee_score(c_sn, c_person):
    headcount = c_sn.attendee_set.count()
    try:
        attendee = c_sn.attendee_set.get(person=c_person)
    except:
        attendee = None
    if attendee == None:
        return "--"
    else:
        return round(get_placement_score_change(attendee, headcount),2)

@register.filter
def check_person_rank(c_sn, c_person):
    try:
        attendee = c_sn.personsnapshot_set.get(person=c_person)
    except:
        attendee = None
    if attendee == None:
        return "--"
    else:
        return attendee.end_rank

@register.filter
def check_person_score(c_sn, c_person):
    try:
        attendee = c_sn.personsnapshot_set.get(person=c_person)
    except:
        attendee = None
    if attendee == None:
        return "--"
    else:
        return attendee.end_score

@register.filter
def py_member_filter(matchups):
    return matchups.filter(py__tag=Person.MEMBER)

@register.filter
def member_filter(people):
    return people.filter(tag=Person.MEMBER)

@register.filter
def retired_filter(people):
    return people.filter(tag=Person.RETIRED)

@register.filter
def get_match_count(match_set, c_sn):
    num_matches = match_set.filter(sn=c_sn).count()
    if num_matches == 0:
        return 1
    return num_matches

@register.filter
def get_matchup(person_x, person_y):
    try:
        matchup = person_x.px_matchup_set.get(py=person_y)
    except:
        matchup = None
    return matchup

@register.filter
def get_smashnights(person, sns_to_include):
    sn_set = []
    attendee_set = person.attendee_set.filter(sn__in=sns_to_include)
    for attendee in attendee_set:
        if attendee.sn not in sn_set:
            sn_set.append(attendee.sn)
    return sn_set
