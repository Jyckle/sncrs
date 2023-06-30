from django.urls import path
from .views import *

urlpatterns = [
    path('', home_view, name='home'),
    path('home/', home_view, name='home'),
    path('week/', week_view, name='week'),
    path('placement_scores/', placement_scores_view, name='placement_scores'),
    path('players/', players_view, name='players'),
    path('matchups/', matchups_view, name='matchups'),
    path('scoring/', scoring_view, name='scoring'),
    path('scoring/<int:c_id>/', scoring_detail_view, name='scoring_detail_view'),
    path('ruleset/', ruleset_view, name='ruleset'),
    path('about/', about_view, name='about'),
    path('venues/', venues_view, name='venues'),
    path('frame_data/', frame_data_view, name='frame_data'),
    path('calendar/', calendar_view, name='calendar'),
]
