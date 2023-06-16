from django_filters import rest_framework as filters
from django.db.models import Q

from data.models import Match

class MatchFilter(filters.FilterSet):
    chat_tag = filters.CharFilter(label='chat_tag', method='both_chat_tags')
    player = filters.CharFilter(label='player', method='both_players')

    class Meta:
        model = Match
        fields = [
            'sn',
            'chat_tag',
            'match_url',
            'player'
        ]
    
    def both_chat_tags(self, queryset, name, value):
        return queryset.filter(
            Q(p1__chat_tag=value) | Q(p2__chat_tag=value)
        )
    
    def both_players(self, queryset, name, value):
        return queryset.filter(
            Q(p1__display_name=value) | Q(p2__display_name=value)
        )