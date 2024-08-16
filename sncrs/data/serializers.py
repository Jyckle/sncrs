from rest_framework import serializers

from data.models import (
    Match, PersonSnapshot, SmashNight,
    Person, Character, Greeting, Matchup, Clip, ClipTag,
    Quote, QuoteTag, QuoteSpeaker, Whine, SocialLink, Site,
    Lesson
)

from data.utility_functions import get_sncrs_person

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

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ('name',)

class SocialLinkSerializer(serializers.ModelSerializer):
    person = display_name_related_serializer()
    site = SiteSerializer()
    class Meta:
        model = SocialLink
        fields = ('person', 'site', 'url', 'id')

class PersonSerializer(serializers.ModelSerializer):
    debut = serializers.ReadOnlyField()
    mains = serializers.SerializerMethodField()
    rivals = serializers.SerializerMethodField()
    all_names = serializers.SerializerMethodField()
    bracket_demon = display_name_related_serializer()
    team = name_related_serializer()
    tag = serializers.CharField(
        source='get_tag_display'
    )
    socials = SocialLinkSerializer(many=True)

    class Meta:
        model = Person
        fields = [
            'id',
            'display_name',
            'all_names',
            'rivals',
            'team',
            'rank',
            'score',
            'bracket_demon',
            'tag',
            'debut',
            'mains',
            'socials',
            ]
    
    def get_mains(self, obj):
        return obj.main_set.all().order_by('order').values_list('character__name', flat=True)

    def get_rivals(self, obj):
        return obj.rivals[:2]
    
    def get_all_names(self, obj):
        return [obj.display_name, *list(obj.alias_set.values_list('name', flat=True))]


class GreetingSerializer(serializers.ModelSerializer):
    person = display_name_related_serializer()

    class Meta:
        model = Greeting
        fields = [
            'id',
            'person',
            'content',
            'name',
            ]


class MatchupSerializer(serializers.ModelSerializer):
    px = display_name_related_serializer()
    py = display_name_related_serializer()
    px_total_game_wins = serializers.ReadOnlyField()
    py_total_game_wins = serializers.ReadOnlyField()
    px_total_set_wins = serializers.ReadOnlyField()
    py_total_set_wins = serializers.ReadOnlyField()
    total_sets = serializers.ReadOnlyField()
    total_games = serializers.ReadOnlyField()

    class Meta:
        model = Matchup
        fields = [
            'px',
            'py',
            'px_total_game_wins',
            'py_total_game_wins',
            'px_total_set_wins',
            'py_total_set_wins',
            'total_sets',
            'total_games', 
        ]


class ClipTagListingField(serializers.RelatedField):
    def to_representation(self, value):
        return value.tag

    def to_internal_value(self, data):
        return data


class ClipTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClipTag
        fields = ['tag']


class ClipSerializer(serializers.ModelSerializer):
    tags = ClipTagListingField(
        many=True,
        queryset=ClipTag.objects.all()
    )

    class Meta:
        model = Clip
        fields = [
            'id',
            'tags',
            'title',
            'url',
            ]
        
    def create(self, validated_data):
        tag_data = validated_data.pop("tags")
        clip = Clip.objects.create(**validated_data)
        for tag in tag_data:
            tag_object, _ = ClipTag.objects.get_or_create(tag=tag)
            clip.tags.add(tag_object.id)
        return clip

class WhineSerializer(serializers.ModelSerializer):
    person = display_name_related_serializer()

    class Meta:
        model = Whine
        fields = [
            'id',
            'name',
            'person',
            'text',
            'url',
            ]

class QuoteTagListingField(serializers.RelatedField):
    def to_representation(self, value):
        return value.tag

    def to_internal_value(self, data):
        return data


class QuoteTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuoteTag
        fields = ['tag']


class QuoteSpeakerListingField(serializers.RelatedField):
    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        return data


class QuoteSerializer(serializers.ModelSerializer):
    speakers = QuoteSpeakerListingField(
        many=True,
        queryset=QuoteSpeaker.objects.all()
    )
    tags = QuoteTagListingField(
        many=True,
        queryset=QuoteTag.objects.all()
    )

    class Meta:
        model = Quote
        fields = [
            'id',
            'text',
            'speakers',
            'tags',
        ]
        
    def create(self, validated_data):
        tag_data = validated_data.pop("tags")
        speaker_data = validated_data.pop("speakers")
        quote = Quote.objects.create(**validated_data)
        for tag in tag_data:
            tag_object, _ = QuoteTag.objects.get_or_create(tag=tag)
            quote.tags.add(tag_object.id)
        for speaker in speaker_data:
            sncrs_person = get_sncrs_person(speaker)
            if sncrs_person is None:
                speaker_object, _ = QuoteSpeaker.objects.update_or_create(name=speaker)
            else:
                speaker = sncrs_person.display_name
                speaker_object, _ = QuoteSpeaker.objects.update_or_create(
                    person=sncrs_person,
                    defaults=dict(
                        name=speaker,
                    ))
            quote.speakers.add(speaker_object.id)
        return quote


class LessonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Lesson
        fields = [
            'id',
            'text',
            'url',
            ]