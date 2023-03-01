# Logic for handling matchups will go here
from .models import MatchupType, Matchup, Person


# helper function for mathchup table
def get_set_history(person_1, person_2):
    win_count = 0
    loss_count = 0
    p1_matches = person_1.p1_match_set.filter(p2=person_2)
    p2_matches = person_1.p2_match_set.filter(p1=person_2)
    for match in p1_matches:
        if match.p1_wins > match.p2_wins:
            win_count += 1
        elif match.p1_wins < match.p2_wins:
            loss_count += 1
    for match in p2_matches:
        if match.p1_wins < match.p2_wins:
            win_count += 1
        elif match.p1_wins > match.p2_wins:
            loss_count += 1
    return win_count, loss_count


# helper function for mathchup table
def get_game_history(person_1, person_2):
    win_count = 0
    loss_count = 0
    p1_matches = person_1.p1_match_set.filter(p2=person_2)
    p2_matches = person_1.p2_match_set.filter(p1=person_2)
    for match in p1_matches:
        win_count += match.p1_wins if match.p1_wins >= 0 else 0
        loss_count += match.p2_wins if match.p2_wins >= 0 else 0
    for match in p2_matches:
        win_count += match.p2_wins if match.p2_wins >= 0 else 0
        loss_count += match.p1_wins if match.p1_wins >= 0 else 0
    return win_count, loss_count


# helper function for matchup table
def get_matchup_type(win_count, loss_count):
    total_count = win_count + loss_count
    if total_count < 2:
        win_percent = -5
    else:
        win_percent = (float(win_count)/float(total_count))*100
    for matchup_type in MatchupType.objects.all():
        if matchup_type.lower_bound <= win_percent < matchup_type.upper_bound:
            return matchup_type
    return None


# given all people, create a matchup table
def create_matchup_table():
    plx = Person.objects.all()
    ply = Person.objects.all()
    for person_x in plx:
        for person_y in ply:
            try:
                c_matchup = Matchup.objects.get(px=person_x, py=person_y)
            except Matchup.DoesNotExist:
                c_matchup = None
            except Matchup.MultipleObjectsReturned:
                print("Error: Multiple matchups found")
                continue

            wins, losses = get_game_history(person_x, person_y)
            set_wins, set_losses = get_set_history(person_x, person_y)

            if c_matchup is None:
                c_matchup_type = get_matchup_type(wins, losses)
                c_set_matchup_type = get_matchup_type(set_wins, set_losses)
                sncrs_match = Matchup(
                    px=person_x,
                    py=person_y,
                    px_wins=wins,
                    py_wins=losses,
                    px_set_wins=set_wins,
                    py_set_wins=set_losses,
                    matchup_type=c_matchup_type,
                    set_matchup_type=c_set_matchup_type)
                sncrs_match.save()
            else:
                c_matchup_type = get_matchup_type(
                    wins+c_matchup.px_additional_wins,
                    losses+c_matchup.py_additional_wins
                )
                c_set_matchup_type = get_matchup_type(
                    set_wins+c_matchup.px_additional_set_wins,
                    set_losses+c_matchup.py_additional_set_wins
                )
                c_matchup.px_wins = wins
                c_matchup.py_wins = losses
                c_matchup.matchup_type = c_matchup_type
                c_matchup.px_set_wins = set_wins
                c_matchup.py_set_wins = set_losses
                c_matchup.set_matchup_type = c_set_matchup_type
                c_matchup.save()
