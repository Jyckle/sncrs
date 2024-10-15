from django.db import models
from django.db.models import Max, F, Value, Q, Count, Case, When, Min, OuterRef, Subquery, Sum
from django.db.models.functions import Lower, Concat, Abs, Coalesce, Cast
from django.db import transaction

import re
import challonge
import os
from typing import Tuple
from collections import defaultdict
from itertools import groupby, combinations

# Create your models here.
class Character(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.URLField(max_length=200, null=True, blank=True)
    character_id = models.IntegerField(null=True, blank=True)
    @property
    def static_image_name(self):
        return "data/characters/" + re.sub(r'[\W]+', '', re.sub('[\W ]+', '_', self.name.lower())) + ".webp"

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name", "character_id"]


class Team(models.Model):
    name = models.CharField(max_length=200)
    tag = models.CharField(max_length=10)
    team_color = models.CharField(max_length=7, default="#FFFFFF")
    logo = models.ImageField(upload_to='team/logo', null=True, blank=True)
    icon = models.ImageField(upload_to='team/icon', null=True, blank=True)

    def __str__(self):
        return self.name

class PersonQuerySet(models.QuerySet):
    """
    A class for operations on a set of :class:`Person` objects.

    If there are methods that operate on a per-person basis, they should
    not be included here.
    """
    def set_debut(self):
        short_title_sq = SmashNight.objects.filter(personsnapshot__person__id=OuterRef('id')).order_by('date').values('short_title')[:1]
        return self.annotate(
            debut=Subquery(short_title_sq)
        )

    def set_best_placement_score(self, sn: 'SmashNight'):
        """Find the best placement score for each person for the provided SmashNight
        """
        best_placement_score = Placement.objects.filter(person=OuterRef('id'), bracket__in=sn.bracket_set.all()).order_by('bracket__rank').values('placement_score')[:1]
        return self.annotate(
            best_placement_score=Subquery(best_placement_score)
        )
    
    def get_person(self, text):
        """
        Returns the database object corresponding to the given text
        or None if there is no such individual.

        Parameters
        ----------
        text : str, required
            The name of the person you would like to find.

        Returns
        -------
        Person or None
            The :class:`Person` object with the given name or alias.
        """
        for person in self.all():
            if person.is_name(text):
                return person
        return None
    
    def set_demons(self):
        """Set bracket demons for the provided group of people"""
        for person in self:
            person.bracket_demon = Person.objects.get(display_name=person.demons[0])
            person.save()
    


class PersonManager(models.Manager.from_queryset(PersonQuerySet)):

    def get_queryset(self):
        return (
            super(PersonManager, self)
            .get_queryset()
            .set_debut()
        )

class Person(models.Model):
    display_name = models.CharField(max_length=100)
    score = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    friend_code = models.CharField(max_length=20, null=True, blank=True)
    bracket_demon = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demon_set'
    )
    mains = models.ManyToManyField(Character, through="PreferredCharacter")

    MEMBER = 0
    GUEST = 1
    RETIRED = 2
    OTHER = 3
    TAG_CHOICES = [
        (MEMBER, "Member"),
        (GUEST, "Guest"),
        (RETIRED, "Retired"),
        (OTHER, "Other")
    ]
    tag = models.IntegerField(null=True, blank=True, choices=TAG_CHOICES)
    ELITE = 0
    CHALLENGER = 1
    OTHER = 3
    STATUS_CHOICES = [
        (ELITE, "Elite"),
        (CHALLENGER, "Challenger"),
        (OTHER, "Other")
    ]
    status = models.IntegerField(choices=STATUS_CHOICES, default=CHALLENGER)

    objects = PersonManager()

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name_plural = "people"
        ordering = [Lower("display_name")]

    @property
    def rivals(self):
        return self.px_matchup_set.order_by('-rival_score').values_list('py__display_name', flat=True)

    @property
    def demons(self):
        return self.px_matchup_set.order_by('-demon_score').values_list('py__display_name', flat=True)

    def get_names(self):
        """
        Returns a list of the names and aliases this Person has.

        Returns
        -------
        names : list
            List of strings that are display name and aliases
        """
        names = [self.display_name]
        names.extend([alias.name for alias in self.alias_set.all()])
        return names

    def is_name(self, check_name):
        """
        Returns a boolean based on whether the given text is a name
        associated with this object or not. All names are lowercase
        for this check

        Parameters
        ----------
        check_name : str, required
            The name to check for this object.

        Returns
        -------
        boolean
            True if this object has the checked name, False otherwise.
        """
        if check_name.lower() in [x.lower() for x in self.get_names()]:
            return True
        else:
            return False

class Alias(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return "{} AKA {}".format(self.name, self.person.display_name)

    class Meta:
        verbose_name_plural = "aliases"

class PreferredCharacter(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="main_set")
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.person}: {self.character}"

    class Meta:
        ordering = ["order"]

    @transaction.atomic
    def update_mains_order(self):
        if self.order is None:
            max_order = self.person.main_set.all().aggregate(Max('order')).get('order__max')
            if max_order is None: max_order = -1
            self.order = max_order + 1

    def save(self, *args, **kwargs):
        self.update_mains_order()
        super().save(*args, **kwargs)
        


class SmashNightQuerySet(models.QuerySet):
    """
    This class handles any operations that impact multiple SmashNight
    objects.
    """

    def get_earliest_sn_in_season(self, season):
        """
        Returns the earliest SmashNight object in the season.

        Parameters
        ----------
        season : int, required
            The number of the season to search.

        Returns
        -------
        SmashNight
            The SmashNight object in the set with the smallest night count.
        """
        return next(iter(self.filter(season=season).order_by('night_count')), None)

    def get_latest_night_count(self):
        """
        Returns the latest night_count of a SmashNight object in the given set.

        Returns
        -------
        night_count: int
            The latest night_count.
        """
        latest_sn = next(iter(self.order_by('-night_count')), None)
        if latest_sn is None:
            return 0
        else:
            return latest_sn.night_count

    def get_latest_season(self) -> int:
        """
        Get the latest season in the QuerySet

        Returns
        -------
        curr_season: int
            The current season
        """
        curr_season = self.aggregate(Max('season')).get('season__max')
        return curr_season

    def set_season_night_count_annotation(self) -> models.QuerySet:
        """
        Annotate SmashNights with the season_night_cound
        The season_night_count is the count of the night within the given season. 
        For instance, even if the overall night count is 50, if it is the first in 
        the season, this will be 1.
        """
        # First, build a subquery that refers to the outer level season
        # Aggregate this by season
        nights_in_season = self.filter(
            season=OuterRef("season")
        ).order_by().values('season')
        # Now, we want the minimum night in the season, based on the night_count
        min_night_in_season = nights_in_season.annotate(
            min_night=Min('night_count')
        ).values('min_night')
        # Finally, combine the current object's night_count with the 
        # minimum night_count to find the night it has within the season
        annotated = self.annotate(
            season_night_count=(
                F('night_count')
                - Subquery(min_night_in_season)
                + 1
            )
        )
        return annotated

    def set_short_title_annotation(self) -> models.QuerySet:
        """
        Annotate smashNights with the short title in the format
        {season}.{season_night_count}
        i.e. 5.2
        """
        annotated = self.annotate(
            short_title=Concat(
                F('season'), 
                Value('.'), 
                F('season_night_count'),
                output_field=models.CharField(),
            )
        )
        return annotated

class SmashNightManager(models.Manager.from_queryset(SmashNightQuerySet)):
    
    def get_queryset(self):
        return (
            super(SmashNightManager, self)
            .get_queryset()
            .set_season_night_count_annotation()
            .set_short_title_annotation()
        )


class SmashNight(models.Model):
    season = models.IntegerField()
    date = models.DateField()
    title = models.CharField(max_length=200, blank=True, null=True)
    night_count = models.IntegerField(blank=True, null=True)
    automations_ran = models.BooleanField(default=False)
    objects = SmashNightManager()

    def __str__(self):
        return "{} on {}".format(self.title, self.date)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.night_count = SmashNight.objects.get_latest_night_count() + 1
            night_in_season = SmashNight.objects.filter(season=self.season).count() + 1
            self.title = f"SmashNight Season {self.season} Night {night_in_season}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "smashnights"
        ordering = ["-date"]

    def create_all_attendee_ranks(self):
        """Record all attendee ranks and start scores"""
        people_with_scores = Person.objects.filter(placement__bracket__in=self.bracket_set.all()).set_best_placement_score(self).distinct().order_by('-score')
        for rank_by_score, person in enumerate(people_with_scores):
            start_seed = rank_by_score + 1
            end_rank = people_with_scores.filter(best_placement_score__lt=person.best_placement_score).distinct().count() + 1
            Attendee.objects.update_or_create(
                sn=self,
                person=person,
                defaults=dict(
                    start_seed=start_seed,
                    end_seed=end_rank,
                    start_score=person.score
                )
            )

    def update_attendee_scores(self):
        """Update the scores for all attendees at this event"""
        for attendee in self.attendee_set.all():
            attendee.update_end_score()
        return
    
    def update_all_challenge_matches(self):
        for c_match in self.match_set.filter(type=Match.CHALLENGE):
            c_match.set_initial_scores()
            c_match.set_score_changes()
        return


class Bracket(models.Model):
    class Type(models.TextChoices):
        STANDARD = "STD", "STANDARD"
        ROUND_ROBIN = "RR", "ROUND_ROBIN" 

    sn = models.ForeignKey(SmashNight, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200, null=True)
    rank = models.IntegerField()
    url = models.URLField(max_length=200, null=True, blank=True)
    bracket_type = models.CharField(max_length=3, choices=Type, default=Type.STANDARD)

    def __str__(self):
        return "{}: Bracket {}, {}".format(self.sn, self.rank, self.title)

    def get_challonge_bracket_data(self) -> Tuple[list, list]:
        # Set up credentials to access challonge account
        challonge.set_credentials(os.environ.get('CHALLONGE_USER'), os.environ.get('CHALLONGE_KEY'))
        # get the challonge tournament
        tournament = challonge.tournaments.show(self.url.replace("https://challonge.com/", ""))
        # get all participants from challonge
        participants = challonge.participants.index(tournament["id"])
        # get all matches from challonge
        matches = challonge.matches.index(tournament["id"])

        return participants, matches


    def create_matches(self):
        participants, matches = self.get_challonge_bracket_data()
        participant_ids = {}
        people = Person.objects
        # add all participants to id list
        for participant in participants:
            sncrs_person = people.get_person(participant["name"])
            if sncrs_person is not None:
                participant_ids[participant["id"]] = sncrs_person

        for match in matches:
            # if there is a score and two valid participants, add an element
            scores_csv = match.get("scores_csv")
            player1 = participant_ids.get(match.get("player1_id", "invalid_player_id"))
            player2 = participant_ids.get(match.get("player2_id", "invalid_player_id"))
            if scores_csv and player1 and player2:
                scores = re.split(r'(?<=\d)-(?=\d)|(?<=\d)-(?=-)', match["scores_csv"])
                sc1 = scores[0]
                sc2 = scores[1]
                match_id = match["id"]
                match_object, created = Match.original_objects.update_or_create(
                    challonge_id=match_id,
                    p1=player1,
                    p2=player2,
                    defaults=dict(
                        p1_wins=sc1,
                        p2_wins=sc2,
                        type=Match.BRACKET,
                        round=match["round"],
                        sn=self.sn,
                        bracket=self,
                    )
                )
                if created:
                    match_object.set_initial_scores()
                match_object.set_score_changes()

    def get_starting_ranks(self) -> dict[int, int]:
        """Get the initial rank for each participant"""
        all_matches = self.match_set.all()
        ordered_people = Person.objects.filter(
            Q(p1_match_set__in=all_matches) |
            Q(p2_match_set__in=all_matches)
        ).distinct().order_by('-score')
        start_ranks = {}
        for start_rank, person in enumerate(ordered_people):
            start_ranks[person.pk] = start_rank
        return start_ranks

    def get_final_ranks(self) -> dict[int, int]:
        """Get the final ranks for each participant"""
        if self.bracket_type == self.Type.ROUND_ROBIN:
            final_ranks = self.get_round_robin_final_ranks()
        else:
            final_ranks = self.get_standard_final_ranks()
        return final_ranks

    def get_round_robin_final_ranks(self) -> dict[int, int]:
        """Get the final ranks for round robin participants"""
        scores = defaultdict(int)
        for match in self.match_set.all():
            # 1000 points for winning the set
            scores[match.winner] += 1000
            # 10 points for each win above the opponent
            scores[match.winner] += 10*(match.winner_games - match.loser_games)
            # 1 point for each game won
            scores[match.winner] += match.winner_games
            scores[match.loser] += match.loser_games
        val_func = lambda x: -x[1]
        sorted_scores = sorted(scores.items(), key=val_func)
        grouped_scores = groupby(sorted_scores, val_func)
        rankings = {}
        for rank, group_and_people in enumerate(grouped_scores):
            for person, _ in group_and_people[1]:
                rankings[person] = rank
        return rankings        
        
    def get_standard_final_ranks(self) -> dict['Person', int]:
        """Get the final ranks for standard bracket participants"""
        final_match = sorted(self.match_set.all(), key=lambda current_match: (-current_match.round, -current_match.challonge_id))[0]
        matches = sorted(self.match_set.all(), key=lambda current_match: current_match.round)
        rankings = {}
        round_winners = []
        round_losers = []
        current_round = 1000
        place = 1
        # Start with the highest match and make that first and second place
        if final_match.winner not in rankings:
            rankings[final_match.winner] = place
            place += 1
        if final_match.loser not in rankings:
            rankings[final_match.loser] = place
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
            if match.winner not in rankings:
                round_winners.append(match.winner)
            if match.loser not in rankings:
                round_losers.append(match.loser)
        return rankings
    
    def create_bracket_ranks(self):
        starting_ranks = self.get_starting_ranks()
        final_ranks = self.get_final_ranks()
        # add all participants to attendees list and create bracket seeding
        for person in final_ranks.keys():
            # create seed and placement in bracket
            self.seed_set.update_or_create(
                person_id=person,
                defaults=dict(
                    seed=starting_ranks[person]
                )
            )
            self.placement_set.update_or_create(
                person_id=person,
                defaults=dict(
                    place=final_ranks[person]
                )
            )

class Seed(models.Model):
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    seed = models.IntegerField(null=True, blank=True)
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE)

    def __str__(self):
        return "{}: {} at {}".format(self.seed, self.person.display_name, self.bracket)

    class Meta:
        ordering = ['bracket', 'seed']


class Placement(models.Model):
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    place = models.IntegerField(null=True, blank=True)
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE)
    placement_score = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return "{}: {} at {}".format(self.place, self.person.display_name, self.bracket)

    class Meta:
        ordering = ['bracket', 'place']

    def save(self, *args, **kwargs):
        """On save, set the placement score

        Placement score is Bracket Rank * 100,000 + Bracket Placement
        This means the top bracket (rank 1) will produce the lowest placement score
        This makes it much easier to calculate overall placement
        """
        self.placement_score = self.bracket.rank * 100_000 + self.place
        if (
            update_fields := kwargs.get("update_fields")
        ) is not None and "place" in update_fields:
            kwargs["update_fields"] = {"placement_score"}.union(update_fields)
        super().save(*args, **kwargs)

class MatchQuerySet(models.QuerySet):

    def set_winners_indices(self):
        return self.annotate(
            winners_index=Count(
                'bracket__match__round',
                filter=Q(
                    bracket__match__round__gt=F('round')
                ),
                distinct=True
            )
        )

    def set_losers_indices(self):
        return self.annotate(
            losers_index=Count(
                'bracket__match__round',
                filter=Q(
                    bracket__match__round__lt=F('round')
                ),
                distinct=True
            )
        )

    def set_round_name(self):
        return self.annotate(
            round_name=Case(
                When(
                    round__gt=0,
                    then=Case(
                        When(winners_index=0, then=Value("Grand Finals")),
                        When(winners_index=1, then=Value("W Finals")),
                        When(winners_index=2, then=Value("W Semis")),
                        When(winners_index=3, then=Value("W Quarters")),
                        default=Concat(
                            Value("Winners "),
                            F('round'),
                            output_field=models.CharField()
                        )
                    )
                ),
                When(
                    round__lt=0,
                    then=Case(
                        When(losers_index=0, then=Value("L Finals")),
                        When(losers_index=1, then=Value("L Semis")),
                        When(losers_index=2, then=Value("L Quarters")),
                        default=Concat(
                            Value("Losers "),
                            Abs(F('round')),
                            output_field=models.CharField(),
                        )
                    )
                ),
                default=Value("")
            )
        )
    
    def set_title(self):
        short_title_sq = SmashNight.objects.filter(id=OuterRef('sn__id')).order_by().values('short_title')
        p1_main_name = PreferredCharacter.objects.filter(person__id=OuterRef('p1__id')).order_by('order').values('character__name')[:1]
        p2_main_name = PreferredCharacter.objects.filter(person__id=OuterRef('p2__id')).order_by('order').values('character__name')[:1]
        return self.annotate(
            title=Concat(
                # First, place our overall SmashNight Data
                Value('STL SN '),
                Subquery(short_title_sq), Value(' '),
                # Then the bracket title and round name if this is a bracket match
                Case(
                    When(
                        type=0, # Bracket Match
                        then=Case(
                            When(
                                bracket__bracket_type=Bracket.Type.STANDARD,
                                then=Concat(
                                    F('bracket__title'),
                                    Value(' '),
                                    F('round_name'),
                                )
                            ),
                            When(
                                bracket__bracket_type=Bracket.Type.ROUND_ROBIN,
                                then=F('bracket__title'),
                            ),
                        ),
                    ), 
                    When(type=1, then=Value('Challenge Match')), # Challenge Match
                    default=Value("")
                ),
                Value('-'),
                # Now the info for player 1
                F('p1__team__tag'), Value(' | '),
                F('p1__display_name'),
                Value('('), Subquery(p1_main_name), Value(')'),
                Value(' vs '),
                # The info for player 2
                F('p2__team__tag'), Value(' | '),
                F('p2__display_name'),
                Value('('), Subquery(p2_main_name), Value(')'),
                output_field=models.CharField()
            )
        )
    
    def set_description(self):
        short_title_sq = SmashNight.objects.filter(id=OuterRef('sn__id')).order_by().values('short_title')
        return self.annotate(
            description=Concat(
                # First, place our overall SmashNight Data
                Subquery(short_title_sq), Value(' | '),
                # Then the bracket title and round name if this is a bracket match
                Case(
                    When(
                        type=0, # Bracket Match
                        then=Case(
                            When(
                                bracket__bracket_type=Bracket.Type.STANDARD,
                                then=Concat(
                                    F('bracket__title'),
                                    Value(' '),
                                    F('round_name'),
                                )
                            ),
                            When(
                                bracket__bracket_type=Bracket.Type.ROUND_ROBIN,
                                then=F('bracket__title'),
                            ),
                        ),
                    ), 
                    When(type=1, then=Value('Challenge Match')), # Challenge Match
                    default=Value("")
                ),
                Value(' | '),
                # Now the info for player 1
                F('p1__display_name'),
                Value(' vs '),
                # The info for player 2
                F('p2__display_name'),
                output_field=models.CharField()
            )
        )
    
    def get_player_game_wins(self, px: Person, py: Person) -> tuple[int, int]:
        """
        Return the total player wins from all matches between these two people

        Parameters
        ----------
        px, py: Person
            The two individuals to check the matches for

        Returns
        -------
        int, int
            px's total game wins, py's total game wins
        """
        aggregated_vals = self.filter(
            p1__in=[px, py], p2__in=[px, py]
        ).aggregate(
            px_wins=Sum(
                Case(
                    When(p1=px, p2=py, then=F('p1_wins')),
                    When(p1=py, p2=px, then=F('p2_wins')),
                    default=0
                )
            ),
            py_wins=Sum(
                Case(
                    When(p1=py, p2=px, then=F('p1_wins')),
                    When(p1=px, p2=py, then=F('p2_wins')),
                    default=0
                )
            ),
        )
        return (
            aggregated_vals['px_wins'],
            aggregated_vals['py_wins'],
        )

    def get_player_set_wins(self, px: Person, py: Person) -> tuple[int, int]:
        """
        Return the total set wins from all matches between these two people
        Should only be used after setting winner and loser annotations

        Parameters
        ----------
        px, py: Person
            The two individuals to check the matches for

        Returns
        -------
        int, int
            px's total set wins, py's total set wins
        """
        aggregated_vals = self.filter(
            p1__in=[px, py], p2__in=[px, py]
        ).aggregate(
            px_wins=Count('pk', filter=Q(winner=px.pk, loser=py.pk)),
            py_wins=Count('pk', filter=Q(winner=py.pk, loser=px.pk)),
        )
        return (
            aggregated_vals['px_wins'],
            aggregated_vals['py_wins'],
        )

    def set_winner_and_loser_annotation(self) -> models.QuerySet:
        """
        Annotate matchups with the id of the winner and loser
        """
        annotated = self.annotate(
            winner=Coalesce(
                Case(
                    When(p1_wins__gt=F('p2_wins'), then=F('p1')),
                    When(p1_wins__lt=F('p2_wins'), then=F('p2')),
                    default=None
                ),
                None
            ),
            loser=Coalesce(
                Case(
                    When(p1_wins__gt=F('p2_wins'), then=F('p2')),
                    When(p1_wins__lt=F('p2_wins'), then=F('p1')),
                    default=None
                ),
                None
            )
        )
        return annotated
    
    def set_winner_and_loser_games(self) -> models.QuerySet:
        """
        Annotate matchups with the games won by winner
        """
        annotated = self.annotate(
            winner_games=Coalesce(
                Case(
                    When(p1_wins__gt=F('p2_wins'), then=F('p1_wins')),
                    When(p1_wins__lt=F('p2_wins'), then=F('p2_wins')),
                    default=None
                ),
                None
            ),
            loser_games=Coalesce(
                Case(
                    When(p1_wins__gt=F('p2_wins'), then=F('p2_wins')),
                    When(p1_wins__lt=F('p2_wins'), then=F('p1_wins')),
                    default=None
                ),
                None
            )
        )
        return annotated


class MatchManager(models.Manager.from_queryset(MatchQuerySet)):

    def get_queryset(self):
        return (
            super(MatchManager, self)
                .get_queryset()
                .set_winners_indices()
                .set_losers_indices()
                .set_round_name()
                .set_title()
                .set_description()
                .set_winner_and_loser_annotation()
                .set_winner_and_loser_games()
        )


class Match(models.Model):
    p1 = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name='p1_match_set', blank=True)
    p2 = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name='p2_match_set', blank=True)
    p1_score = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    p2_score = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    p1_wins = models.IntegerField(null=True, blank=True)
    p2_wins = models.IntegerField(null=True, blank=True)
    p1_score_change = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    p2_score_change = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    sn = models.ForeignKey(SmashNight, on_delete=models.SET_NULL, null=True, blank=True)
    bracket = models.ForeignKey(Bracket, on_delete=models.SET_NULL, null=True, blank=True)
    challonge_id = models.IntegerField(null=True, blank=True)
    match_url = models.URLField(max_length=200, null=True, blank=True)
    round = models.IntegerField(null=True, blank=True)
    objects = MatchManager()
    original_objects = models.Manager()

    BRACKET = 0
    CHALLENGE = 1
    CREW = 2
    OTHER = 3
    TYPE_CHOICES = [
        (BRACKET, "Bracket Match"),
        (CHALLENGE, "Challenge Match"),
        (CREW, "Crew Battle"),
        (OTHER, "Other")
    ]
    type = models.IntegerField(null=True, blank=True, choices=TYPE_CHOICES)

    def __str__(self):
        return "{} vs. {} at {}: {}".format(
            self.p1,
            self.p2,
            self.sn,
            self.pk
        )

    class Meta:
        verbose_name_plural = "matches"
    
    def set_score_changes(self):
        """
        Set the changes in score according to the player scores and match results.
        """
        if int(self.p1_wins) == -1 or int(self.p2_wins) == -1:
            self.p1_score_change = 0
            self.p2_score_change = 0
        elif self.p1_wins > self.p2_wins:
            self.p1_score_change = 5 * (1 - 1 / (1 + 5.0 ** ((float(self.p2_score) - float(self.p1_score)) / 80)))
            self.p2_score_change = -3 * (1 / (1 + 10.0 ** ((float(self.p1_score) - float(self.p2_score)) / 80)))
        else:
            self.p1_score_change = -3 * (1 / (1 + 10.0 ** ((float(self.p2_score) - float(self.p1_score)) / 80)))
            self.p2_score_change = 5 * (1 - 1 / (1 + 5.0 ** ((float(self.p1_score) - float(self.p2_score)) / 80)))
        self.save()

    def set_initial_scores(self):
        """Set initial_scores to those of the registered players"""
        self.p1_score = self.p1.score
        self.p2_score = self.p2.score
        self.save()

class Attendee(models.Model):
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True)
    sn = models.ForeignKey(SmashNight, on_delete=models.SET_NULL, null=True)
    start_seed = models.IntegerField(null=True, blank=True)
    end_seed = models.IntegerField(null=True, blank=True)
    start_score = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    end_score = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return "{} at {}".format(self.person, self.sn)

    class Meta:
        ordering = ['sn__date']

    def get_placement_score_change(self):
        """Get the score change based on overall placement"""
        points = 5.0 if self.person.status == Person.ELITE else 0.0
        if self.start_seed >= self.end_seed:
            points += (self.start_seed - self.end_seed + 0.5) * 30 / self.sn.attendee_set.count() + 3
        return points

    def update_end_score(self):
        """Update the final score based on the starting score,
        matches played, and placement score
        """
        # get current score
        current_score = self.start_score
        # add all changes for match sets
        p1_matches = self.person.p1_match_set.filter(sn=self.sn)
        p2_matches = self.person.p2_match_set.filter(sn=self.sn)
        for match in p1_matches:
            current_score += match.p1_score_change
        for match in p2_matches:
            current_score += match.p2_score_change
        # add placement score changes
        current_score = float(current_score) + self.get_placement_score_change()
        self.end_score = max(current_score, 60.0)
        self.save()


class StageType(models.Model):
    name = models.CharField(max_length=100)
    display_color = models.CharField(max_length=7, default="#FFFFFF")

    def __str__(self):
        return self.name


class Stage(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='stages', null=True, blank=True)
    type = models.ForeignKey(StageType, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

class MatchupTypeQuerySet(models.QuerySet):
    """
    A class for operations on a set of :class:`MatchupType` objects.

    If there are methods that operate on a per-matchupType basis, they should
    not be included here.
    """

    def get_type_by_percent(self, win_percent: float):
        """
        Get the MatchupType by the win percent

        Parameters
        ----------
        win_percent: float
            The win percent to fetch a MatchupType for

        Returns
        -------
        MatchupType
            The MatchupType object matching the win_percent

        """
        return self.get(lower_bound__lte=win_percent, upper_bound__gt=win_percent)

class MatchupType(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    lower_bound = models.DecimalField(max_digits=10, decimal_places=2)
    upper_bound = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=7, default="#FFFFFF")
    objects = MatchupTypeQuerySet.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["lower_bound"]


class PersonSnapshot(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    sn = models.ForeignKey(SmashNight, on_delete=models.CASCADE)
    start_rank = models.IntegerField(null=True, blank=True)
    end_rank = models.IntegerField(null=True, blank=True)
    start_score = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    end_score = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return "{} at {}".format(self.person.display_name, self.sn.title)

    class Meta:
        ordering = ["sn__date", "person__team", "person__display_name"]


class MatchupQuerySet(models.QuerySet):
    """
    A class for operations on a set of :class:`Matchup` objects.

    If there are methods that operate on a per-matchup basis, they should
    not be included here.
    """

    def safe_get_matchup(self, px: Person, py: Person):
        """
        Get the matchup based on two people in a safe manner. If it does not exist,
        return None, else, return the matchup.

        Parameters
        ----------
        px, py: Person

        Returns
        -------
        matchup: Matchup
            The found matchup, or None
        """
        try:
            c_matchup = self.get(px=px, py=py)
            return c_matchup
        except Matchup.MultipleObjectsReturned:
            print(f"Error: Multiple matchups found between {px.display_name} and {py.display_name}")
        except Matchup.DoesNotExist:
            pass
        return None

    def safe_get_matchup_wins(self, px: Person, py: Person) -> tuple[int, int]:
        """
        Check if there are any exceptions with a specific matchup and return total wins if not

        Parameters
        ----------
        px, py: Person
            The people to find a matchup for

        Returns
        -------
        int, int
            px_total_wins, py_total_wins, or None, None
        """
        c_matchup = self.safe_get_matchup(px, py)
        if not c_matchup:
            return None, None
        px_total_wins, py_total_wins = c_matchup.get_total_wins()
        if px_total_wins == 0 and py_total_wins == 0:
            return None, None
        return px_total_wins, py_total_wins

    def set_total_game_wins_annotation(self) -> models.QuerySet:
        """
        Annotate matchups with the total number of wins
        """
        annotated = self.annotate(
            px_total_game_wins=Coalesce(F('px_wins') + F('px_additional_wins'), 0),
            py_total_game_wins=Coalesce(F('py_wins') + F('py_additional_wins'), 0),
        )
        return annotated

    def set_total_set_wins_annotation(self) -> models.QuerySet:
        """
        Annotate matchups with the total number of wins
        """
        annotated = self.annotate(
            px_total_set_wins=Coalesce(F('px_set_wins') + F('px_additional_set_wins'), 0),
            py_total_set_wins=Coalesce(F('py_set_wins') + F('py_additional_set_wins'), 0),
        )
        return annotated

    def set_total_sets_annotation(self) -> models.QuerySet:
        """
        Annotate matchups with the total number of games played
        """
        total_set_wins_annotated = self.set_total_set_wins_annotation()
        annotated = total_set_wins_annotated.annotate(
            total_sets=Coalesce(F('px_total_set_wins') + F('py_total_set_wins'), 0)
        )
        return annotated

    def set_total_games_annotation(self) -> models.QuerySet:
        """
        Annotate matchups with the total number of games played
        """
        total_wins_annotated = self.set_total_game_wins_annotation()
        annotated = total_wins_annotated.annotate(
            total_games=Coalesce(F('px_total_game_wins') + F('py_total_game_wins'), 0)
        )
        return annotated

    def set_rival_score_annotation(self) -> models.QuerySet:
        """
        Annotate matchups with the rival score
        This score indicates the status of person y as a rival to person x
        with higher values indicating person y is more likely to be a rival for person x
        """
        total_wins_annotated = self.set_total_game_wins_annotation()
        annotated = total_wins_annotated.annotate(
            rival_score=Cast(
                Coalesce(
                    Case(
                        When(px_total_game_wins=0.0, py_total_game_wins=0.0, then=-1000.0),
                        default=(
                            5.0 * (F('px_total_game_wins') + F('py_total_game_wins')) -
                            6.0 * Abs(F('px_total_game_wins') - F('py_total_game_wins'))
                        )
                    ),
                    -1000.0
                ),
                output_field=models.FloatField())
        )
        return annotated

    def set_demon_score_annotation(self) -> models.QuerySet:
        """
        Annotate matchups with the demon score
        This score indicates the status of person y as a demon to person x
        with higher values indicating person y is more likely to be the demon for person x
        """
        total_wins_annotated = self.set_total_game_wins_annotation()
        annotated = total_wins_annotated.annotate(
            demon_score=Cast(
                Coalesce(
                    Case(
                        When(px_total_game_wins=0.0, py_total_game_wins=0.0, then=-1000.0),
                        When(px_total_game_wins__lt=F('py_total_game_wins'),
                             then=(F('py_total_game_wins') - F('px_total_game_wins') / 10.0)),
                        default=F('py_total_game_wins') * 25.0 - F('px_total_game_wins') * 13.0
                    ),
                    -1000.0
                ),
                output_field=models.FloatField())
        )
        return annotated

    def set_rank_difference_annotation(self) -> models.QuerySet:
        """
        Annotate matchups with the rank difference between the two players
        """
        annotated = self.annotate(rank_difference=Abs(F('px__rank') - F('py__rank')))
        return annotated

    def set_game_win_percent_annotation(self) -> models.QuerySet:
        """
        Annotate matchups with the game win percent of px
        """
        total_wins_annotated = self.set_total_game_wins_annotation()
        total_games_annotated = total_wins_annotated.set_total_games_annotation()
        annotated = total_games_annotated.annotate(
            game_win_percent=Case(
                When(total_games__lt=2, then=-5.0),
                default=(
                    (F('px_total_game_wins') * 1.0) / (F('total_games') * 1.0)
                ) * 100.0
            )
        )
        return annotated

    def set_set_win_percent_annotation(self) -> models.QuerySet:
        """
        Annotate matchups with the set win percent of px
        """
        total_set_wins_annotated = self.set_total_set_wins_annotation()
        total_sets_annotated = total_set_wins_annotated.set_total_sets_annotation()
        annotated = total_sets_annotated.annotate(
            set_win_percent=Case(
                When(total_sets__lt=2, then=-5.0),
                default=(
                    (F('px_total_set_wins') * 1.0) / (F('total_sets') * 1.0)
                ) * 100.0
            )
        )
        return annotated

    def set_matchup_types(self):
        """
        Set the game and set matchup type for each matchup
        """
        for matchup in self:
            matchup.matchup_type = MatchupType.objects.get_type_by_percent(matchup.game_win_percent)
            matchup.set_matchup_type = MatchupType.objects.get_type_by_percent(matchup.set_win_percent)
            matchup.save()

    def create_or_update_matchups_table(self, person_list: models.QuerySet = None) -> None:
        """
        Create or update the full matchups table with the given person_list
        During this process, do not overwrite additional_wins, as that is a manually entered value

        Parameters
        ----------
        person_list: models.QuerySet
            The list of people to generate the matchup table for. If not provided, defaults to all people
        """
        person_list = person_list or Person.objects.all()
        match_queryset = Match.objects
        for person_x, person_y in combinations(person_list, 2):
            px_wins, py_wins = match_queryset.get_player_game_wins(person_x, person_y)
            px_set_wins, py_set_wins = match_queryset.get_player_set_wins(person_x, person_y)
            self.update_or_create(
                px=person_x,
                py=person_y,
                defaults=dict(
                    px_wins=px_wins,
                    py_wins=py_wins,
                    px_set_wins=px_set_wins,
                    py_set_wins=py_set_wins,
                )
            )
            self.update_or_create(
                py=person_x,
                px=person_y,
                defaults=dict(
                    py_wins=px_wins,
                    px_wins=py_wins,
                    py_set_wins=px_set_wins,
                    px_set_wins=py_set_wins,
                )
            )
        self.set_matchup_types()

class MatchupManager(models.Manager.from_queryset(MatchupQuerySet)):

    def get_queryset(self):
        return super(MatchupManager, self).get_queryset()\
            .set_rival_score_annotation()\
            .set_demon_score_annotation()\
            .set_rank_difference_annotation()\
            .set_game_win_percent_annotation()\
            .set_set_win_percent_annotation()

class Matchup(models.Model):
    px = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name='px_matchup_set')
    py = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name='py_matchup_set')
    px_wins = models.IntegerField(null=True, blank=True)
    py_wins = models.IntegerField(null=True, blank=True)
    px_additional_wins = models.IntegerField(default=0, blank=True)
    py_additional_wins = models.IntegerField(default=0, blank=True)
    px_set_wins = models.IntegerField(null=True, blank=True)
    py_set_wins = models.IntegerField(null=True, blank=True)
    px_additional_set_wins = models.IntegerField(default=0, blank=True)
    py_additional_set_wins = models.IntegerField(default=0, blank=True)
    matchup_type = models.ForeignKey(MatchupType, on_delete=models.SET_NULL, null=True, related_name='game_matchup_set')
    set_matchup_type = models.ForeignKey(
        MatchupType,
        on_delete=models.SET_NULL,
        null=True,
        related_name='set_matchup_set'
    )
    objects = MatchupManager()

    def __str__(self):
        return "{} vs. {}".format(self.px, self.py)

    class Meta:
        ordering = ["py__display_name"]
    
    def get_total_wins(self) -> tuple[int, int]:
        """
        Get the total wins for each person in the matchup

        Returns
        -------
        px_total_wins: int, py_total_wins: int
        """
        return self.px_wins + self.px_additional_wins, self.py_wins + self.py_additional_wins


class Venue(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField()

    def __str__(self):
        return str(self.name)

class VenueImage(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to=f'venues')
    venue = models.ForeignKey(Venue, related_name='images', on_delete=models.DO_NOTHING)

class Greeting(models.Model):
    name = models.CharField(max_length=255)
    content = models.TextField()
    person = models.ForeignKey(Person, null=True, blank=True, related_name="greetings", on_delete=models.DO_NOTHING)

    def save(self, *args, **kwargs):
        if not self.pk:
            person_to_assign = Person.objects.filter(Q(display_name__iexact=self.name) | Q(alias__name__iexact=self.name)).distinct()
            if len(person_to_assign) == 1:
                self.person = person_to_assign[0]
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name}: {self.content}"

class ClipTag(models.Model):
    tag = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.tag

class Clip(models.Model):
    url = models.URLField(max_length=200, null=True, blank=True)
    title = models.TextField()
    tags = models.ManyToManyField(ClipTag, related_name='clips')

    def __str__(self):
        return f"{self.title}: {' | '.join(self.tags.values_list('tag', flat=True))}"

class Whine(models.Model):
    text = models.TextField()
    name = models.CharField(max_length=255)
    person = models.ForeignKey(Person, null=True, blank=True, related_name="whines", on_delete=models.DO_NOTHING)
    url = models.URLField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.name}: {self.text}"

class Site(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name    

class SocialLink(models.Model):
    site = models.ForeignKey(Site, related_name="social_links", on_delete=models.CASCADE)
    url = models.URLField(max_length=200, null=True, blank=True)
    person = models.ForeignKey(Person, related_name="socials", on_delete=models.CASCADE)


class QuoteTag(models.Model):
    tag = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.tag
    
class QuoteSpeaker(models.Model):
    name = models.CharField(max_length=255)
    person = models.ForeignKey(Person, null=True, blank=True, related_name="speakers", on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.name

class Quote(models.Model):
    text = models.TextField()
    tags = models.ManyToManyField(QuoteTag, related_name='quotes')
    speakers = models.ManyToManyField(QuoteSpeaker, related_name='quotes')

    def __str__(self):
        return f"\"{self.text}\" -{' -'.join(self.speakers.values_list('name', flat=True))} ({' | '.join(self.tags.values_list('tag', flat=True))})"
    
class Lesson(models.Model):
    text = models.TextField()
    url = models.URLField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.text
