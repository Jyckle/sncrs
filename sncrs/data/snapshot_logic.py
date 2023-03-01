# snapshot_logic.py

# Person snapshot logic
# For every person, create an entry with name and smashNight and start score
# Get start rank from current scores
# Then, after updates, get end rank from end_scores

from .models import Person
from .utility_functions import assign_score_based_ranks


# Store the current scores of each person in a snapshot
def store_scores(c_sn, score_type):
    # calculate current ranks
    people = Person.objects.filter(tag=Person.MEMBER)
    assign_score_based_ranks(people)

    # if start of smashNight, store current values in new snapshots
    if score_type == "start":
        for c_person in people:
            # check for existing element and add if none
            snapshot_count = c_sn.personsnapshot_set.filter(person=c_person, sn=c_sn).count()
            if snapshot_count <= 0:
                c_sn.personsnapshot_set.create(
                    person=c_person,
                    sn=c_sn,
                    start_rank=c_person.rank,
                    start_score=c_person.score
                )
    # if end of smashNight store
    elif score_type == "end":
        for c_person in people:
            # check for existing element and add if none
            try:
                c_snapshot = c_sn.personsnapshot_set.get(person=c_person, sn=c_sn)
            except Exception:
                c_snapshot = None
            if c_snapshot is not None:
                c_snapshot.end_rank = c_person.rank
                c_snapshot.end_score = c_person.score
                c_snapshot.save()

    return
