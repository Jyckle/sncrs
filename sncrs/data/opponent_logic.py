from .models import Person, Matchup


def get_opponent_score(person_a, person_b, opponent_score_type):
    opponent_score = -1000
    try:
        c_matchup = Matchup.objects.get(px=person_a, py=person_b)
    except Matchup.DoesNotExist:
        return opponent_score
    except Matchup.MultipleObjectsReturned:
        print("Error: Multiple matchups found")
        return opponent_score

    px_total_wins = c_matchup.px_wins + c_matchup.px_additional_wins
    py_total_wins = c_matchup.py_wins + c_matchup.py_additional_wins
    if px_total_wins == 0 and py_total_wins == 0:
        return opponent_score

    # for the rivals, let us consider both the number of matches played
    # and how close the record is
    if opponent_score_type == "rival":
        opponent_score = 5*(px_total_wins + py_total_wins) - 6*abs(px_total_wins-py_total_wins)
    # for the demon, if the matchup is favorable, score far more on opponent wins
    # if the matchup is unfavorable, score only a bit more on enemy wins
    elif opponent_score_type == "demon":
        if px_total_wins >= py_total_wins:
            opponent_score = py_total_wins - px_total_wins/10
        else:
            opponent_score = py_total_wins*25 - px_total_wins*13
    return opponent_score


def get_rank_difference(person_a, person_b):
    return abs(person_a.rank - person_b.rank)


def get_demon(person_a):
    person_list = Person.objects.filter(tag=Person.MEMBER)
    scores = {}
    for person_b in person_list:
        scores[person_b] = (-get_opponent_score(person_a, person_b, "demon"), get_rank_difference(person_a, person_b))
    demons = [demon for (demon, value) in sorted(scores.items(), key=lambda x: (x[1][0], x[1][1]))]
    return demons[0]


def set_all_demons():
    person_list = Person.objects.filter(tag=Person.MEMBER)
    for person in person_list:
        demon = get_demon(person)
        person.bracket_demon = demon
        person.save()
    return
