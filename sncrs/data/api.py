from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from data.views import MatchList, SnapshotList, SmashNightList, PersonList

urlpatterns = [
    path('matches/', MatchList.as_view(), name='matches'),
    path('snapshots/', SnapshotList.as_view(), name='snapshots'),
    path('smashnights/', SmashNightList.as_view(), name='smashnights'),
    path('people/', PersonList.as_view(), name='people')
]

urlpatterns = format_suffix_patterns(urlpatterns)