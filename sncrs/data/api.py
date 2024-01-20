from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

from data.views import (
    MatchList, SnapshotList, SmashNightList, PersonList,
    GreetingList, MatchupList, ClipList, ClipDeleteView, WhineList
)

urlpatterns = [
    path('matches/', MatchList.as_view(), name='matches'),
    path('snapshots/', SnapshotList.as_view(), name='snapshots'),
    path('smashnights/', SmashNightList.as_view(), name='smashnights'),
    path('people/', PersonList.as_view(), name='people'),
    path('greetings/', GreetingList.as_view(), name='greetings'),
    path('matchups/', MatchupList.as_view(), name='matchups'),
    path('clips/', ClipList.as_view(), name='clips'),
    path('clip/<int:pk>/', ClipDeleteView.as_view(), name='clip'),
    path('whines/', WhineList.as_view(), name='whines'),
    path('auth/', include('rest_framework.urls'))
]

urlpatterns = format_suffix_patterns(urlpatterns)