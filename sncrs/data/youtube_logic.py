import re
import os

import googleapiclient.discovery
import googleapiclient.errors

from .models import SmashNight, Match


def get_night_count(sn=None, match=None):
    night = 0
    if sn is not None:
        earliest_smash_night = SmashNight.objects.filter(season=sn.season).order_by('night_count')[0]
        night = sn.night_count - earliest_smash_night.night_count + 1
    elif match is not None:
        earliest_smash_night = SmashNight.objects.filter(season=match.sn.season).order_by('night_count')[0]
        night = match.sn.night_count - earliest_smash_night.night_count + 1
    return night


# get the match title for YouTube
def get_match_title(match):
    title = ""
    bracket_format = "STL SmashNight {season}.{night} {bracket_title} {win_lose} "\
        "Round {round}- {team_1} | {p1}({p1_main}) vs {team_2} | {p2}({p2_main})"
    challenge_format = "STL SmashNight {season}.{night} "\
        "Challenge Match- {team_1} | {p1}({p1_main}) vs {team_2} | {p2}({p2_main})"
    if match.type == Match.BRACKET:
        title = bracket_format.format(
            season=match.sn.season,
            night=get_night_count(match=match),
            bracket_title=match.bracket.title,
            win_lose="Winners" if match.round > 0 else "Losers" if match.round < 0 else "",
            round=abs(match.round),
            team_1=match.p1.team.tag,
            team_2=match.p2.team.tag,
            p1=match.p1.display_name,
            p2=match.p2.display_name,
            p1_main=match.p1.main_1.name if match.p1.main_1 is not None else "",
            p2_main=match.p2.main_1.name if match.p2.main_1 is not None else ""
        )
    elif match.type == Match.CHALLENGE:
        title = challenge_format.format(
            season=match.sn.season,
            night=get_night_count(match=match),
            team_1=match.p1.team.tag,
            team_2=match.p2.team.tag,
            p1=match.p1.display_name,
            p2=match.p2.display_name,
            p1_main=match.p1.main_1.name if match.p1.main_1 is not None else "",
            p2_main=match.p2.main_1.name if match.p2.main_1 is not None else ""

        )
    return title


# get the match description for YouTube
def get_match_description(match):
    desc = ""
    if match.type == Match.BRACKET:
        desc = "S{season}T{night} | {bracket_title}, {win_lose} Round {round} | {p1} vs {p2}".format(
            season=match.sn.season,
            night=get_night_count(match=match),
            bracket_title=match.bracket.title,
            win_lose="Winners" if match.round > 0 else "Losers" if match.round < 0 else "",
            round=abs(match.round),
            p1=match.p1.display_name,
            p2=match.p2.display_name
        )
    elif match.type == Match.CHALLENGE:
        desc = "S{season}T{night} | Challenge Match | {p1} vs {p2}".format(
            season=match.sn.season,
            night=get_night_count(match=match),
            p1=match.p1.display_name,
            p2=match.p2.display_name
        )

    return desc


# get title and description for all matches
def get_titles_and_descriptions(sn):
    all_details = []
    for match in sn.match_set.all():
        all_details.append(
            {
                "Title": get_match_title(match),
                "Description": get_match_description(match)
            }
        )
    return all_details


# get the round number given the Description
def get_round_number(description):
    extracted_round = re.search(r'(?<=round )\d', description)
    if extracted_round is not None:
        round_number = 0
    else:
        round_number = int(extracted_round.group(0))

    if 'loser' in description:
        return -round_number
    else:
        return round_number


# get all videos from a smashNight
def get_smashnight_videos(sn):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    # os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=os.environ.get('SNCRS_YOUTUBE_DEV_KEY'))

    current_season_night_count = get_night_count(sn=sn)
    search_string = "{0}.{1}".format(sn.season, current_season_night_count)

    request = youtube.search().list(
        part="snippet",
        channelId=os.environ.get('SNCRS_YOUTUBE_CHANNEL_ID'),
        maxResults=50,
        q=search_string,
        type="video"
    )
    response = request.execute()

    return response["items"]


# assign YouTube video to a match
def get_possible_matches(video, sn):
    title = video['snippet']['title'].lower()
    description = video['snippet']['description'].lower()
    matches = []
    for match in sn.match_set.all():
        # Check if there is a match with aliases/names of both players
        p1_names = [match.p1.display_name]
        p1_names.extend([alias.name for alias in match.p1.alias_set.all()])
        p2_names = [match.p2.display_name]
        p2_names.extend([alias.name for alias in match.p2.alias_set.all()])
        # Check if the description and title matches
        if any(item.lower() in title for item in p1_names) and any(item.lower() in title for item in p2_names):
            if get_match_description(match).lower() in description:
                matches.append(match)

    return matches


# assign all videos from a smashnight
def set_videos(sn):
    videos = get_smashnight_videos(sn)
    for video in videos:
        matches = get_possible_matches(video, sn)
        if len(matches) == 1:
            match = matches[0]
            match.match_url = "https://youtube.com/watch?v=" + video['id']['videoId']
            match.save()
    return
