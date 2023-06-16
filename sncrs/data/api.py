from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from data.views import *

urlpatterns = [
    path('matches/', MatchList.as_view(), name='matches'),
]

urlpatterns = format_suffix_patterns(urlpatterns)