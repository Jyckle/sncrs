from django.shortcuts import render, get_object_or_404
from django.db.models import Func, F
from django.db.models.functions import Lower

from data.models import Match, PersonSnapshot, Person, Team, StageType, SmashNight
from data.serializers import MatchSerializer, SnapshotSerializer
from data.filters import MatchFilter, SnapshotFilter
from rest_framework import generics


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
    latest_brackets = SmashNight.objects.latest('date').bracket_set.order_by('rank')
    snapshot_set = sorted(
        SmashNight.objects.latest('date').personsnapshot_set.all(),
        key=lambda k: -1*(k.end_score - k.start_score)
    )
    score_sorted_snapshots = sorted(
        SmashNight.objects.latest('date').personsnapshot_set.all(),
        key=lambda k: -1*k.end_score
    )
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
    return render(request, "data/venues.html", {})


def frame_data_view(request, *args, **kwargs):
    return render(request, "data/frame_data.html", {})


def about_view(request, *args, **kwargs):
    return render(request, "data/about.html", {})


def calendar_view(request, *args, **kwargs):
    return render(request, "data/calendar.html", {})


class MatchList(generics.ListAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    filterset_class = MatchFilter

class SnapshotList(generics.ListAPIView):
    queryset = PersonSnapshot.objects.all()
    serializer_class = SnapshotSerializer
    filterset_class = SnapshotFilter