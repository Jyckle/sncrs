from django.forms import ModelForm
from django.forms.widgets import TextInput
from .models import Team, StageType, MatchupType


class TeamForm(ModelForm):
    class Meta:
        model = Team
        fields = "__all__"
        widgets = {
            "team_color": TextInput(attrs={"type": "color"}),
        }


class StageTypeForm(ModelForm):
    class Meta:
        model = StageType
        fields = "__all__"
        widgets = {
            "display_color": TextInput(attrs={"type": "color"}),
        }


class MatchupTypeForm(ModelForm):
    class Meta:
        model = MatchupType
        fields = "__all__"
        widgets = {
            "color": TextInput(attrs={"type": "color"}),
        }
