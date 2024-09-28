# snapshot_logic.py

# Person snapshot logic
# For every person, create an entry with name and smashNight and start score
# Get start rank from current scores
# Then, after updates, get end rank from end_scores

from .models import Person, SmashNight, PersonSnapshot
from .utility_functions import assign_score_based_ranks


# Store the current scores of each person in a snapshot
def store_previous_snapshot_or_current_scores(c_sn, score_type):
    # calculate current ranks
    people = Person.objects.filter(tag=Person.MEMBER)
    previous_sn_in_season = SmashNight.objects.exclude(pk=c_sn.pk).filter(season=c_sn.season).order_by('-night_count').first()
    if score_type == "start" and previous_sn_in_season:
        for c_person in people:
            try:
                previous = PersonSnapshot.objects.get(person=c_person, sn=previous_sn_in_season)
                c_person.score=previous.end_score
                c_person.save()
            except PersonSnapshot.DoesNotExist:
                pass
        # Reload to get the new scores
        people = Person.objects.all().filter(tag=Person.MEMBER)
    assign_score_based_ranks(people)

    for c_person in people:
        if score_type == "start":
            update_vals = {
                "start_rank": c_person.rank,
                "start_score": c_person.score,
            }
        elif score_type == "end":
            update_vals = {
                "end_rank": c_person.rank,
                "end_score": c_person.score,
            }
        c_sn.personsnapshot_set.update_or_create(
            person=c_person,
            sn=c_sn,
            defaults=update_vals
        )
