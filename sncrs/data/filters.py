from django_filters import rest_framework as filters
from django.db.models import Q

from data.models import (
    Match, PersonSnapshot, SmashNight, Person,
    Greeting, Matchup, Clip, ClipTag, Quote, QuoteTag, Whine, SocialLink,
)

class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass

class MatchFilter(filters.FilterSet):
    player = filters.CharFilter(label='player', field_name='display_name', method='both_players_filter')
    season = filters.CharFilter(label='season', field_name='sn__season')
    sn_title = filters.CharFilter(label='sn_title', field_name='short_title', method='short_title_filter')

    class Meta:
        model = Match
        fields = [
            'sn',
            'match_url',
        ]
    
    def both_players_filter_single(self, queryset, name, value):
        """Create a query filtering both p1 and p2 on the field
        specified by field_name, for the value in value"""
        player = value
        p1_arg = {f'p1__{name}': player}
        p2_arg = {f'p2__{name}': player}
        return queryset.filter(Q(**p1_arg) | Q(**p2_arg))
    
    def both_players_filter(self, queryset, name, value):
        """Allow multiple players to be specified by using
        commas as a separator"""
        players = value.split(",")
        filtered_set = queryset
        for player in players:
            filtered_set = self.both_players_filter_single(filtered_set, name, player)
        return filtered_set
    
    def short_title_filter(self, queryset, name, value):
        sn = SmashNight.objects.filter(**{name: value}).first()
        return queryset.filter(Q(sn=sn))
    
class SnapshotFilter(filters.FilterSet):
    player = filters.CharFilter(label='player', field_name="person__display_name")

    class Meta:
        model = PersonSnapshot
        fields = [
            'sn',
        ]

class SmashNightFilter(filters.FilterSet):
    short_title = filters.CharFilter(label='short_title', field_name="short_title")

    class Meta:
        model = SmashNight
        fields = [
            'night_count',
        ]
    
class PersonFilter(filters.FilterSet):
    debut = filters.CharFilter(label='debut', field_name="debut")
    name = filters.CharFilter(label='name', method='all_names_filter')

    class Meta:
        model = Person
        fields = [
            'display_name',
            'tag',
            'team',
            'name',
        ]
    
    def all_names_filter(self, queryset, name, value):
        """Create a query filtering both display name and aliases on the field
        specified by field_name, for the value in value"""
        player = valueSocialLink
        display_name_arg = {f'display_name__iexact': player}
        alias_arg = {f'alias__name__iexact': player}
        return queryset.filter(Q(**display_name_arg) | Q(**alias_arg)).distinct()


class GreetingFilter(filters.FilterSet):
    person = filters.CharFilter(label='person', field_name="person__display_name", lookup_expr="iexact")
    name = filters.CharFilter(label='name', lookup_expr="iexact")
    content = filters.CharFilter(label='content', lookup_expr="icontains")

    class Meta:
        model = Greeting
        fields = [
            'person',
            'name',
            'content',
        ]


class MatchupFilter(filters.FilterSet):
    px = filters.CharFilter(label='px', field_name="px__display_name", lookup_expr="iexact")
    py = filters.CharFilter(label='py', field_name="py__display_name", lookup_expr="iexact")

    class Meta:
        model = Matchup
        fields = [
            'px',
            'py',
        ]


class ClipFilter(filters.FilterSet):
    tags = filters.CharFilter(label='tags', field_name="tags__tag", lookup_expr="iexact")
    title = filters.CharFilter(label='title', lookup_expr="icontains")

    class Meta:
        model = Clip
        fields = [
            'id',
            'title',
            'tags',
        ]


class WhineFilter(filters.FilterSet):
    person = filters.CharFilter(label='person', field_name="person__display_name", lookup_expr="iexact")
    name = filters.CharFilter(label='name', lookup_expr="iexact")
    text = filters.CharFilter(label='content', lookup_expr="icontains")

    class Meta:
        model = Whine
        fields = [
            'person',
            'name',
            'text',
        ]


class SocialLinkFilter(filters.FilterSet):
    site = filters.CharFilter(label='site', field_name="site__name", lookup_expr="iexact")
    person__in = CharInFilter(label='person__in', field_name="person__display_name", lookup_expr="in")

    class Meta:
        model = SocialLink
        fields = {
            'site',
            'person',
        }

class QuoteFilter(filters.FilterSet):
    tags = filters.CharFilter(label='tags', field_name="tags__tag", lookup_expr="iexact")
    speakers = filters.CharFilter(label='speakers', field_name="speakers__name", lookup_expr="iexact")
    text = filters.CharFilter(label='text', lookup_expr="icontains")

    class Meta:
        model = Quote
        fields = [
            'id',
            'text',
            'speakers',
            'tags',
        ]
