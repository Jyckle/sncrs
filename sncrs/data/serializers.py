from rest_framework import serializers

from data.models import Match, PersonSnapshot, SmashNight, Person, Character

display_name_related_serializer = lambda: serializers.SlugRelatedField(
    allow_null=True,
    read_only=True,
    slug_field='display_name'
)
name_related_serializer = lambda: serializers.SlugRelatedField(
    allow_null=True,
    read_only=True,
    slug_field='name'
)

class MatchSerializer(serializers.ModelSerializer):
    p1 = display_name_related_serializer()
    p2 = display_name_related_serializer()
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
    person = display_name_related_serializer()
    sn = serializers.SlugRelatedField(
        allow_null=True,
        read_only=True,
        slug_field='title'
    )
    
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
    

class PersonSerializer(serializers.ModelSerializer):
    debut = serializers.ReadOnlyField()
    mains = serializers.SerializerMethodField()
    rivals = serializers.SerializerMethodField()
    bracket_demon = display_name_related_serializer()
    team = name_related_serializer()
    tag = serializers.CharField(
        source='get_tag_display'
    )

    class Meta:
        model = Person
        fields = [
            'id',
            'display_name',
            'chat_tag',
            'rivals',
            'team',
            'rank',
            'score',
            'bracket_demon',
            'tag',
            'debut',
            'mains',
            ]
    
    def get_mains(self, obj):
        return obj.main_set.all().order_by('order').values_list('character__name', flat=True)

    def get_rivals(self, obj):
        return obj.rivals[:2]
