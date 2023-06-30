# Bracket Logic
# For each bracket, the code will input start and end seeds for each person

from .utility_functions import get_challonge_bracket_data, get_sncrs_person


# get the final rank of a participant
def get_final_bracket_ranks(c_bracket):
    final_match = sorted(c_bracket.match_set.all(), key=lambda current_match: (-current_match.round, -current_match.challonge_id))[0]
    matches = sorted(c_bracket.match_set.all(), key=lambda current_match: current_match.round)
    rankings = {}
    round_winners = []
    round_losers = []
    current_round = 1000
    place = 1
    # Start with the highest match and make that first and second place
    if final_match.p1_wins > final_match.p2_wins:
        if final_match.p1 not in rankings:
            rankings[final_match.p1] = place
            place += 1
        if final_match.p2 not in rankings:
            rankings[final_match.p2] = place
            place += 1
    elif final_match.p1_wins < final_match.p2_wins:
        if final_match.p2 not in rankings:
            rankings[final_match.p2] = place
            place += 1
        if final_match.p1 not in rankings:
            rankings[final_match.p1] = place
            place += 1
    # for the rest of the matches, work down the losers bracket,
    # adding new people at the same seed
    for match in matches:
        # check if within the same round or not
        if match.round != current_round:
            current_round = match.round
            for participant in round_winners:
                rankings[participant] = place
            place += len(round_winners)
            round_winners = []
            for participant in round_losers:
                rankings[participant] = place
            place += len(round_losers)
            round_losers = []
        # add any new participants
        if match.p1 not in rankings:
            if match.p1_wins > match.p2_wins:
                round_winners.append(match.p1)
            else:
                round_losers.append(match.p1)
        if match.p2 not in rankings:
            if match.p2_wins > match.p1_wins:
                round_winners.append(match.p2)
            else:
                round_losers.append(match.p2)

    return rankings


# create bracket seeds and placements for a challonge participant
def create_bracket_places(participant, sncrs_person, c_bracket, final_rankings):
    seed_count = c_bracket.seed_set.filter(person=sncrs_person).count()
    place_count = c_bracket.placement_set.filter(person=sncrs_person).count()

    # if no final rank from challonge, calculate it ourselves
    if participant["final_rank"] is None:
        final_rank = final_rankings[sncrs_person]
    else:
        final_rank = participant["final_rank"]

    if seed_count <= 0:
        c_bracket.seed_set.create(
            person=sncrs_person,
            seed=participant["seed"]
        )
    elif seed_count == 1:
        obj = c_bracket.seed_set.get(person=sncrs_person)
        obj.seed = participant["seed"]
        obj.save()

    if place_count <= 0:
        c_bracket.placement_set.create(
            person=sncrs_person,
            place=final_rank
        )
    elif place_count == 1 and final_rank not in [None, ""]:
        obj = c_bracket.placement_set.get(person=sncrs_person)
        obj.place = final_rank
        obj.save()
    return


# create the ranks for all smashNight Brackets
def create_all_bracket_ranks(sn):
    for c_bracket in sn.bracket_set.all():
        participants, matches = get_challonge_bracket_data(c_bracket)
        final_rankings = get_final_bracket_ranks(c_bracket)
        # add all participants to attendees list and create bracket seeding
        for participant in participants:
            sncrs_person = get_sncrs_person(participant["name"])
            if sncrs_person is not None:
                # create seed and placement in bracket
                create_bracket_places(participant, sncrs_person, c_bracket, final_rankings)
