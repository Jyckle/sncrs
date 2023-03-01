# attendee_logic.py

# Attendee Logic
# People are added as attendees.
# Start seeds and end seeds are calculated based on bracket data
# Start and end brackets are based on rank of brackets

from .models import Attendee
from .utility_functions import get_placement_score_change


# records attendee ranks and start scores
def create_all_attendee_ranks(c_sn):
    c_rank = 1
    last_rank = 1
    end_ranks = {}
    new_parts = []
    for c_bracket in c_sn.bracket_set.order_by('rank'):
        # loop through each bracket ordered by place
        for c_place in c_bracket.placement_set.order_by('place'):
            if c_place.person not in end_ranks and c_place.person not in new_parts:
                # if the place is the same as the last rank, add it to the list to add
                if c_place.place == last_rank:
                    new_parts.append(c_place.person)
                # if a new rank, add the old ranks, adjust the rank counter, and add to list to add
                else:
                    for part in new_parts:
                        end_ranks[part] = c_rank
                    c_rank += len(new_parts)
                    last_rank = c_place.place
                    new_parts = [c_place.person]
        if len(new_parts) > 0:
            for part in new_parts:
                end_ranks[part] = c_rank

    # start ranks are just based on initial scores
    attendees = [person for person in end_ranks]
    sorted_attendees = sorted(attendees, key=lambda person: -person.score)
    start_ranks = {person: ind+1 for ind, person in enumerate(sorted_attendees)}

    # now that all ranks are stored, add attendees with their ranks
    for c_person in attendees:
        try:
            c_attendee = Attendee.objects.get(sn=c_sn, person=c_person)
        except Exception:
            c_attendee = None

        if c_attendee is None:
            attendee = Attendee(
                person=c_person,
                sn=c_sn,
                start_seed=start_ranks[c_person],
                end_seed=end_ranks[c_person],
                start_score=c_person.score
            )
            attendee.save()
        else:
            c_attendee.start_seed = start_ranks[c_person]
            c_attendee.end_seed = end_ranks[c_person]
            c_attendee.save()

    return


# method to update all attendee scores
def update_attendee_scores(c_sn):
    headcount = c_sn.attendee_set.count()
    for attendee in c_sn.attendee_set.all():
        # get current score
        current_score = attendee.start_score
        # add all changes for match sets
        p1_matches = attendee.person.p1_match_set.filter(sn=c_sn)
        p2_matches = attendee.person.p2_match_set.filter(sn=c_sn)
        for match in p1_matches:
            current_score += match.p1_score_change
        for match in p2_matches:
            current_score += match.p2_score_change
        # add placement score changes
        current_score = float(current_score) + get_placement_score_change(attendee, headcount)
        attendee.end_score = max(current_score, 60.0)
        attendee.save()
    return
