from django.db import models
from django.db.models import Max, F, Value, Q, Count, Case, When, Min, OuterRef, Subquery
from django.db.models.functions import Lower, Concat

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

    def __str__(self):
        return self.name


class Person(models.Model):
    display_name = models.CharField(max_length=100)
    score = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    friend_code = models.CharField(max_length=20, null=True, blank=True)
    rival_1 = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name='rival_1_set')
    rival_2 = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name='rival_2_set')
    bracket_demon = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demon_set'
    )
    main_1 = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True, related_name='main_1_set')
    main_2 = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True, related_name='main_2_set')
    main_3 = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True, related_name='main_3_set')

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

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name_plural = "people"
        ordering = [Lower("display_name")]


class Alias(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return "{} AKA {}".format(self.name, self.person.display_name)

    class Meta:
        verbose_name_plural = "aliases"

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
    title = models.CharField(max_length=200)
    night_count = models.IntegerField()
    automations_ran = models.BooleanField(default=False)
    objects = SmashNightManager()

    def __str__(self):
        return "{} on {}".format(self.title, self.date)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.night_count = SmashNight.objects.get_latest_night_count() + 1
            self.title = f"Season {self.season} Night {self.get_season_night_count()}"
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

