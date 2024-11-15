from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

from data.views import (
    MatchList, SnapshotList, SmashNightList, PersonList,
    GreetingList, MatchupList, ClipList, ClipTagList,
    ClipDeleteEditView, QuoteList, QuoteDeleteView, QuoteTagList,
    WhineList,SocialLinkList, LessonList,
)

urlpatterns = [
    path('matches/', MatchList.as_view(), name='matches'),
    path('snapshots/', SnapshotList.as_view(), name='snapshots'),
    path('smashnights/', SmashNightList.as_view(), name='smashnights'),
    path('people/', PersonList.as_view(), name='people'),
    path('greetings/', GreetingList.as_view(), name='greetings'),
    path('matchups/', MatchupList.as_view(), name='matchups'),
    path('clips/', ClipList.as_view(), name='clips'),
    path('clip_tags', ClipTagList.as_view(), name='clip_tags'),
    path('clip/<int:pk>/', ClipDeleteEditView.as_view(), name='clip'),
    path('whines/', WhineList.as_view(), name='whines'),
    path('quotes/', QuoteList.as_view(), name='quotes'),
    path('quote_tags', QuoteTagList.as_view(), name='quote_tags'),
    path('quote/<int:pk>/', QuoteDeleteView.as_view(), name='quote'),
    path('auth/', include('rest_framework.urls')),
    path('socials/', SocialLinkList.as_view(), name='socials'),
    path('lessons/', LessonList.as_view(), name='lessons'),
]

urlpatterns = format_suffix_patterns(urlpatterns)