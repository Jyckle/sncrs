from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext
from django.shortcuts import render

from itertools import chain

from .models import (
    Alias, Seed, Placement, Attendee, Bracket,
    VenueImage, Venue, Character, PreferredCharacter,
    Person, SmashNight, Team, Match, StageType, Stage,
    MatchupType, Matchup, PersonSnapshot, Greeting, Clip, 
    ClipTag, QuoteTag, QuoteSpeaker, Quote, Whine, SocialLink, Site,
    Lesson,
)

from .forms import TeamForm, StageTypeForm, MatchupTypeForm
from .sn_calculate import full_update
from .youtube_logic import set_videos
# Register your models here.


class AliasInline(admin.TabularInline):
    model = Alias

class GreetingInline(admin.TabularInline):
    model = Greeting

class WhineInline(admin.TabularInline):
    model = Whine

class SocialLinkInLine(admin.TabularInline):
    model = SocialLink

class PreferredCharacterInline(admin.TabularInline):
    model = PreferredCharacter

class PersonAdmin(admin.ModelAdmin):
    inlines = [
        AliasInline,
        PreferredCharacterInline,
        GreetingInline,
        WhineInline,
        SocialLinkInLine,
    ]


class SeedInline(admin.TabularInline):
    model = Seed


class PlacementInline(admin.TabularInline):
    model = Placement


class BracketAdmin(admin.ModelAdmin):
    inlines = [
        SeedInline,
        PlacementInline
    ]


class AttendeeInline(admin.StackedInline):
    model = Attendee


class BracketInline(admin.TabularInline):
    model = Bracket


class SmashNightAdmin(admin.ModelAdmin):
    inlines = [
        BracketInline,
        AttendeeInline
    ]
    actions = ['full_update_selected', 'show_youtube_details', 'set_youtube_videos']

    @admin.action(description="Get all data associated with the selected SmashNights and update scores")
    def full_update_selected(self, request, queryset):
        count = 0
        for sn in queryset.order_by('-date'):
            full_update(sn)
            count += 1
        self.message_user(request, ngettext(
            '%d SmashNight was successfully updated.',
            '%d SmashNights were successfully updated.',
            count,
        ) % count, messages.SUCCESS)

    @admin.action(description="Show youtube titles and descriptions")
    def show_youtube_details(self, request, queryset):
        details = []
        for sn in queryset.order_by('-date'):
            for match in chain(
                sn.match_set.filter(bracket__isnull=False).order_by('-bracket__rank', 'round'),
                sn.match_set.filter(bracket__isnull=True)
            ):
                details.append("Title: {}".format(match.title))
                details.append("Description: {}".format(match.description))
                details.append("-------------------------")
        context = {
            "list": details,
            "title": "Youtube Details"
        }
        return render(request, "data/simple_display.html", context)

    @admin.action(description="Set the youtube videos for a smashNight")
    def set_youtube_videos(self, request, queryset):
        count = 0
        for sn in queryset.order_by('-date'):
            set_videos(sn)
            count += 1
        self.message_user(request, ngettext(
            '%d SmashNight was successfully updated.',
            '%d SmashNights were successfully updated.',
            count,
        ) % count, messages.SUCCESS)


class TeamAdmin(admin.ModelAdmin):
    form = TeamForm


class StageTypeAdmin(admin.ModelAdmin):
    form = StageTypeForm


class MatchupTypeAdmin(admin.ModelAdmin):
    form = MatchupTypeForm

class VenueImageAdmin(admin.StackedInline):
    model = VenueImage

class VenueAdmin(admin.ModelAdmin):
    inlines = [VenueImageAdmin]
    class Meta:
        model = Venue
    
class ClipAdmin(admin.ModelAdmin):
    filter_horizontal = ('tags', )
    class Meta:
        model = Clip

class QuoteAdmin(admin.ModelAdmin):
    filter_horizontal = ('tags', 'speakers')
    class Meta:
        model = Quote

admin.site.register(Character)
admin.site.register(Team, TeamAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(SmashNight, SmashNightAdmin)
admin.site.register(Bracket, BracketAdmin)
admin.site.register(Match)
admin.site.register(Attendee)
admin.site.register(Alias)
admin.site.register(Greeting)
admin.site.register(Whine)
admin.site.register(Site)
admin.site.register(SocialLink)
admin.site.register(PreferredCharacter)
admin.site.register(Seed)
admin.site.register(Placement)
admin.site.register(StageType, StageTypeAdmin)
admin.site.register(Stage)
admin.site.register(MatchupType, MatchupTypeAdmin)
admin.site.register(PersonSnapshot)
admin.site.register(Matchup)
admin.site.register(VenueImage)
admin.site.register(Venue, VenueAdmin)
admin.site.register(ClipTag)
admin.site.register(Clip, ClipAdmin)
admin.site.register(QuoteTag)
admin.site.register(QuoteSpeaker)
admin.site.register(Quote, QuoteAdmin)
admin.site.register(Lesson)
