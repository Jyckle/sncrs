from django.shortcuts import render, get_object_or_404
from django.db.models import Func, F
from django.db.models.functions import Lower

from data.models import (
    Match, PersonSnapshot, Person, Team,
    StageType, SmashNight, Venue, Greeting,
    Matchup, Clip, ClipTag, Quote, QuoteTag, Whine, 
    SocialLink, Lesson,
)
from data.serializers import (
    MatchSerializer, SnapshotSerializer, SmashNightSerializer,
    PersonSerializer, GreetingSerializer, MatchupSerializer, ClipSerializer,
    ClipTagSerializer, QuoteSerializer, QuoteTagSerializer, WhineSerializer,
    SocialLinkSerializer, LessonSerializer,
)
from data.filters import (
    MatchFilter, SnapshotFilter, SmashNightFilter, PersonFilter,
    GreetingFilter, MatchupFilter, ClipFilter, QuoteFilter, WhineFilter,
    SocialLinkFilter, LessonFilter,
)
from rest_framework import generics, permissions


def initialize_sn_set(request):
    season_list = [str(item) for item in
                   SmashNight.objects.order_by('-season').values_list('season', flat=True).distinct()]
    season_list.append('All')
    if request.method == 'POST':
        season_selection = request.POST.get('season-select')
    else:
        season_selection = season_list[0]
    if season_selection == 'All':
        smashnight_set = SmashNight.objects.order_by('date')
    else:
        smashnight_set = SmashNight.objects.filter(season=season_selection).order_by('date')
    return season_list, smashnight_set, season_selection


def home_view(request, *args, **kwargs):
    person_queryset = Person.objects.filter(tag=Person.MEMBER).order_by("-score")
    team_queryset = Team.objects.exclude(name="GUEST")
    try:
        latest_sn = SmashNight.objects.latest('date')
        latest_brackets = latest_sn.bracket_set.order_by('rank')
        snapshot_set = sorted(
            latest_sn.personsnapshot_set.all(),
            key=lambda k: -1*(k.end_score - k.start_score)
        )
        score_sorted_snapshots = sorted(
            latest_sn.personsnapshot_set.all(),
            key=lambda k: -1*k.end_score
        )
    except SmashNight.DoesNotExist:
        latest_brackets = []
        snapshot_set = []
        score_sorted_snapshots = []

    context = {
        "person_list": person_queryset,
        "team_list": team_queryset,
        "latest_brackets": latest_brackets,
        "snapshot_set": snapshot_set,
        "score_sorted_snapshots": score_sorted_snapshots
    }
    return render(request, "data/home.html", context)


def week_view(request, *args, **kwargs):
    season_list, smashnight_set, season_selection = initialize_sn_set(request)
    person_list = Person.objects.filter(tag=Person.MEMBER).order_by('team', 'display_name')
    column_count = smashnight_set.count()*2 + 1
    context = {
        "smashnight_set": smashnight_set,
        "person_list": person_list,
        "column_count": column_count,
        "season_list": season_list,
        "season_selection": season_selection
    }
    return render(request, "data/week.html", context)


def placement_scores_view(request, *args, **kwargs):
    season_list, smashnight_set, season_selection = initialize_sn_set(request)
    person_list = Person.objects.filter(tag=Person.MEMBER).order_by('team', 'display_name')
    column_count = smashnight_set.count()*3 + 1
    context = {
        "smashnight_set": smashnight_set,
        "person_list": person_list,
        "column_count": column_count,
        "season_list": season_list,
        "season_selection": season_selection
    }
    return render(request, "data/placement_scores.html", context)


def players_view(request, *args, **kwargs):
    person_list = Person.objects.filter(tag=Person.MEMBER)
    context = {
        "person_list": person_list
    }
    return render(request, "data/players.html", context)


def matchups_view(request, *args, **kwargs):
    person_list = Person.objects.filter(tag=Person.MEMBER).order_by(Lower('display_name'))
    context = {
        "person_list": person_list
    }
    return render(request, "data/matchups.html", context)


def scoring_view(request, *args, **kwargs):
    person_list = Person.objects.filter(tag=Person.MEMBER).order_by('team', 'display_name')
    context = {
        "person_list": person_list
    }
    return render(request, "data/scoring.html", context)


def scoring_detail_view(request, c_id):
    season_list, smashnight_set, season_selection = initialize_sn_set(request)
    c_person = get_object_or_404(Person, id=c_id)
    matches = Match.objects.filter(p1=c_person, sn__in=smashnight_set) | \
        Match.objects.filter(p2=c_person, sn__in=smashnight_set)
    matches = matches.annotate(abs_round=Func(F('round'), function='ABS'))\
        .order_by('sn__date', '-bracket__rank', 'abs_round', '-round')
    column_count = matches.count() + 1
    context = {
        "smashnight_set": smashnight_set,
        "c_person": c_person,
        "column_count": column_count,
        "matches": matches,
        "season_list": season_list,
        "season_selection": season_selection
    }
    return render(request, "data/scoring_detail.html", context)


def ruleset_view(request, *args, **kwargs):
    stage_types = StageType.objects.all()
    context = {
        "stage_types": stage_types
    }
    return render(request, "data/ruleset.html", context)


def venues_view(request, *args, **kwargs):
    venues = Venue.objects.all()
    context = {
        "venues": venues
    }
    return render(request, "data/venues.html", context)


def frame_data_view(request, *args, **kwargs):
    return render(request, "data/frame_data.html", {})


def about_view(request, *args, **kwargs):
    return render(request, "data/about.html", {})


def calendar_view(request, *args, **kwargs):
    return render(request, "data/calendar.html", {})

def hotkeys_view(request, hotkey_type: str, *args, **kwargs):
    context = {
        "hotkey_path": f"data/hotkeys/{hotkey_type}.png",
        "hotkey_type": hotkey_type
    }
    return render(request, "data/hotkeys.html", context)


class MatchList(generics.ListAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    filterset_class = MatchFilter

class SnapshotList(generics.ListAPIView):
    queryset = PersonSnapshot.objects.all()
    serializer_class = SnapshotSerializer
    filterset_class = SnapshotFilter

class SmashNightList(generics.ListAPIView):
    queryset = SmashNight.objects.all()
    serializer_class = SmashNightSerializer
    filterset_class = SmashNightFilter

class PersonList(generics.ListAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    filterset_class = PersonFilter

class GreetingList(generics.ListAPIView):
    queryset = Greeting.objects.all()
    serializer_class = GreetingSerializer
    filterset_class = GreetingFilter

class MatchupList(generics.ListAPIView):
    queryset = Matchup.objects.all()
    serializer_class = MatchupSerializer
    filterset_class = MatchupFilter

class ClipList(generics.ListCreateAPIView):
    queryset = Clip.objects.all()
    serializer_class = ClipSerializer
    filterset_class = ClipFilter
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ClipTagList(generics.ListCreateAPIView):
    queryset = ClipTag.objects.all()
    serializer_class = ClipTagSerializer

class ClipDeleteEditView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Clip.objects.all()
    serializer_class = ClipSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class WhineList(generics.ListAPIView):
    queryset = Whine.objects.all()
    serializer_class = WhineSerializer
    filterset_class = WhineFilter

class SocialLinkList(generics.ListAPIView):
    queryset = SocialLink.objects.all()
    serializer_class = SocialLinkSerializer
    filterset_class = SocialLinkFilter

class QuoteList(generics.ListCreateAPIView):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    filterset_class = QuoteFilter
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class QuoteTagList(generics.ListCreateAPIView):
    queryset = QuoteTag.objects.all()
    serializer_class = QuoteTagSerializer

class QuoteDeleteView(generics.RetrieveDestroyAPIView):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class LessonList(generics.ListAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    filterset_class = LessonFilter
