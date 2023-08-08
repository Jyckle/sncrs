from django.db import models
from django.db.models import Max, F, Value, Q, Count, Case, When, Min, OuterRef, Subquery, Sum
from django.db.models.functions import Lower, Concat, Abs, Coalesce, Cast
from django.db import transaction

import re


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
    chat_tag = models.CharField(max_length=35, null=True, blank=True)

    objects = PersonManager()

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name_plural = "people"
        ordering = [Lower("display_name")]

    @property
    def rivals(self):
        return self.px_matchup_set.order_by('-rival_score').values_list('py__display_name', flat=True)

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

class Bracket(models.Model):
    sn = models.ForeignKey(SmashNight, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200, null=True)
    rank = models.IntegerField()
    url = models.URLField(max_length=200, null=True, blank=True)

    def __str__(self):
        return "{}: Bracket {}, {}".format(self.sn, self.rank, self.title)


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

    def __str__(self):
        return "{}: {} at {}".format(self.place, self.person.display_name, self.bracket)

    class Meta:
        ordering = ['bracket', 'place']

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
                        When(winners_index=1, then=Value("Winners Finals")),
                        When(winners_index=2, then=Value("Winners Semis")),
                        When(winners_index=3, then=Value("Winners Quarters")),
                        default=Concat(
                            Value("Winners Round "),
                            F('round'),
                            output_field=models.CharField()
                        )
                    )
                ),
                When(
                    round__lt=0,
                    then=Case(
                        When(losers_index=0, then=Value("Losers Finals")),
                        When(losers_index=1, then=Value("Losers Semis")),
                        When(losers_index=2, then=Value("Losers Quarters")),
                        default=Concat(
                            Value("Losers Round "),
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
                Value('STL SmashNight '),
                Subquery(short_title_sq), Value(' '),
                # Then the bracket title and round name if this is a bracket match
                Case(
                    When(
                        type=0, # Bracket Match
                        then=Concat(
                            F('bracket__title'),
                            Value(' '),
                            F('round_name'),
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
                        then=Concat(
                            F('bracket__title'),
                            Value(' '),
                            F('round_name'),
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
        aggregated_vals = self.aggregate(
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

        Parameters
        ----------
        px, py: Person
            The two individuals to check the matches for

        Returns
        -------
        int, int
            px's total set wins, py's total set wins
        """
        aggregated_vals = self.aggregate(
            px_wins=Count('pk', filter=Q(p1=px, p2=py, p1_wins__gt=F('p2_wins'))) 
            + Count('pk', filter=Q(p1=py, p2=px, p2_wins__gt=F('p1_wins'))),
            py_wins=Count('pk', filter=Q(p1=py, p2=px, p1_wins__gt=F('p2_wins')))
            + Count('pk', filter=Q(p1=px, p2=py, p2_wins__gt=F('p1_wins'))),
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


class MatchupType(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    lower_bound = models.DecimalField(max_digits=10, decimal_places=2)
    upper_bound = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=7, default="#FFFFFF")

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

class MatchupManager(models.Manager.from_queryset(MatchupQuerySet)):

    def get_queryset(self):
        return super(MatchupManager, self).get_queryset()\
            .set_rival_score_annotation()

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