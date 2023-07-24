import re
import os

import googleapiclient.discovery
import googleapiclient.errors

from .models import SmashNight, Match

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

    title = sn.objects.filter(id=sn.id).first().short_title

    request = youtube.search().list(
        part="snippet",
        channelId=os.environ.get('SNCRS_YOUTUBE_CHANNEL_ID'),
        maxResults=50,
        q=title,
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
            if match.description.lower() in description:
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
