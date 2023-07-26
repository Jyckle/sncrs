from django_filters import rest_framework as filters
from django.db.models import Q

from data.models import Match, PersonSnapshot, SmashNight

class MatchFilter(filters.FilterSet):
    chat_tag = filters.CharFilter(label='chat_tag', field_name='chat_tag', method='both_players_filter')
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
    chat_tag = filters.CharFilter(label='chat_tag', field_name="person__chat_tag")
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
