from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from data.views import MatchList, SnapshotList, SmashNightList

urlpatterns = [
    path('matches/', MatchList.as_view(), name='matches'),
    path('snapshots/', SnapshotList.as_view(), name='snapshots'),
    path('smashnights/', SmashNightList.as_view(), name='smashnights'),
]

urlpatterns = format_suffix_patterns(urlpatterns)