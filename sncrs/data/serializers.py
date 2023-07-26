from rest_framework import serializers

from data.models import Match, PersonSnapshot, SmashNight

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = [
            'id', 
            'p1',
            'p2',
            'p1_score',
            'p2_score',
            'p1_wins',
            'p2_wins', 
            'p1_score_change',
            'p2_score_change',
            'sn',
            'bracket',
            'challonge_id',
            'match_url',
            'round',
            'type',
            ]

class SmashNightSerializer(serializers.ModelSerializer):
    season_night_count = serializers.ReadOnlyField()
    short_title = serializers.ReadOnlyField()

    class Meta:
        model = SmashNight
        fields = [
            'id', 
            'season',
            'date',
            'title',
            'night_count',
            'season_night_count',
            'short_title',
            ]
        
class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonSnapshot
        fields = [
            'id',
            'person',
            'sn',
            'start_rank',
            'end_rank',
            'start_score',
            'end_score',
            ]