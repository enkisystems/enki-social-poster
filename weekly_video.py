import os
import random
import requests
import json
from datetime import datetime, timedelta, timezone

# =========================================================
# CONFIG
# =========================================================

API_URL = "https://api.buffer.com/graphql"

VIDEO_FOLDER = "./videos"
CAPTION_FILE = "captions.txt"

BASE_VIDEO_URL = (
    "https://raw.githubusercontent.com/"
    "enkisystems/enki-social-poster/main/videos/"
)

# =========================================================
# AUTH
# =========================================================

TOKEN = os.getenv("BUFFER_ACCESS_TOKEN") or os.getenv("BUFFER_API_KEY")

if not TOKEN:
    print("\n❌ ERROR: Missing BUFFER_ACCESS_TOKEN / BUFFER_API_KEY")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# =========================================================
# GRAPHQL HELPER
# =========================================================

def graphql(query, variables=None):

    response = requests.post(
        API_URL,
        json={
            "query": query,
            "variables": variables or {}
        },
        headers=HEADERS
    )

    print("\n===================================")
    print("STATUS:", response.status_code)

    try:
        data = response.json()

    except Exception:
        print(response.text)
        raise

    print(json.dumps(data, indent=2))

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]

# =========================================================
# GET ORGANIZATION
# =========================================================

org_query = """
query {
  account {
    organizations {
      id
      name
    }
  }
}
"""

org_data = graphql(org_query)

orgs = org_data["account"]["organizations"]

if not orgs:
    raise Exception("No organizations found")

org_id = orgs[0]["id"]

print("\n✅ Using organization:", orgs[0]["name"])

# =========================================================
# GET CHANNELS
# =========================================================

channels_query = """
query ($orgId: OrganizationId!) {
  channels(input: { organizationId: $orgId }) {
    id
    name
    service
  }
}
"""

channels_data = graphql(
    channels_query,
    {"orgId": org_id}
)

channels = channels_data["channels"]

print("\n✅ Connected channels:")

for channel in channels:
    print(channel)

# =========================================================
# FILTER CHANNELS
# =========================================================

supported_channels = []

for channel in channels:

    service = channel["service"].lower()

    if service in [
        "instagram",
        "facebook",
        "tiktok"
    ]:
        supported_channels.append(channel)

print("\n✅ Video-supported channels:")
print(len(supported_channels))

# =========================================================
# RANDOM VIDEO
# =========================================================

all_videos = [
    file for file in os.listdir(VIDEO_FOLDER)
    if file.lower().endswith((
        ".mp4",
        ".mov",
        ".m4v"
    ))
]

if not all_videos:
    raise Exception("No videos found")

selected_video = random.choice(all_videos)

VIDEO_URL = BASE_VIDEO_URL + selected_video

# =========================================================
# RANDOM CAPTION
# =========================================================

with open(CAPTION_FILE, "r", encoding="utf-8") as file:

    captions = [
        line.strip()
        for line in file.readlines()
        if line.strip() and line.strip() != "========="
    ]

if not captions:
    raise Exception("No captions found")

selected_caption = random.choice(captions)

print("\n✅ Selected video:", selected_video)
print("✅ Selected caption:", selected_caption)
print("✅ Video URL:", VIDEO_URL)

# =========================================================
# SCHEDULE TIME
# =========================================================

now = datetime.now(timezone.utc)

scheduled = now.replace(
    hour=22,
    minute=30,
    second=0,
    microsecond=0
)

if scheduled <= now:
    scheduled += timedelta(days=1)

# +/- 20 minute jitter
scheduled += timedelta(
    minutes=random.randint(-20, 20)
)

scheduled_iso = scheduled.isoformat()

print("\n✅ Scheduled time UTC:", scheduled_iso)

# =========================================================
# CREATE POST MUTATION
# =========================================================

mutation = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {

    ... on PostActionSuccess {
      post {
        id
        text
        dueAt
      }
    }

    ... on MutationError {
      message
    }

  }
}
"""

# =========================================================
# SEND POST
# =========================================================

def send_post(channel, payload):

    print("\n===================================")
    print(
        f"🚀 Posting "
        f"{channel['service']} "
        f"({channel['name']})"
    )

    print(json.dumps(payload, indent=2))

    try:

        result = graphql(
            mutation,
            {"input": payload}
        )

        create_post = result.get("createPost", {})

        if "message" in create_post:

            print("\n❌ BUFFER ERROR:")
            print(create_post["message"])

        else:

            print("\n✅ POST SUCCESS")
            print(json.dumps(result, indent=2))

    except Exception as error:

        print(f"\n❌ FAILED on {channel['service']}")
        print(error)

# =========================================================
# BUILD VIDEO POST PAYLOAD
# =========================================================

def build_video_post_payload(channel):

    service = channel["service"].lower()

    payload = {
        "channelId": channel["id"],

        "text": selected_caption,

        "schedulingType": "automatic",

        "mode": "customScheduled",

        "dueAt": scheduled_iso,

        "assets": [
            {
                "video": {
                    "url": VIDEO_URL
                }
            }
        ]
    }

    # -----------------------------------------
    # INSTAGRAM REEL
    # -----------------------------------------

    if service == "instagram":

        payload["metadata"] = {
            "instagram": {
                "type": "reel",
                "shouldShareToFeed": True
            }
        }

    # -----------------------------------------
    # FACEBOOK REEL
    # -----------------------------------------

    elif service == "facebook":

        payload["metadata"] = {
            "facebook": {
                "type": "reel"
            }
        }

    return payload

# =========================================================
# BUILD STORY PAYLOAD
# =========================================================

def build_story_payload(channel):

    service = channel["service"].lower()

    payload = {
        "channelId": channel["id"],

        "text": "",

        "schedulingType": "automatic",

        "mode": "customScheduled",

        "dueAt": scheduled_iso,

        "assets": [
            {
                "video": {
                    "url": VIDEO_URL
                }
            }
        ]
    }

    # -----------------------------------------
    # INSTAGRAM STORY
    # -----------------------------------------

    if service == "instagram":

        payload["metadata"] = {
            "instagram": {
                "type": "story",
                "shouldShareToFeed": True
            }
        }

    # -----------------------------------------
    # FACEBOOK STORY
    # -----------------------------------------

    elif service == "facebook":

        payload["metadata"] = {
            "facebook": {
                "type": "story"
            }
        }

    return payload

# =========================================================
# POST TO CHANNELS
# =========================================================

print("\n===================================")
print("🎬 POSTING WEEKLY VIDEO")
print("===================================")

for channel in supported_channels:

    service = channel["service"].lower()

    # -----------------------------------------
    # VIDEO POST / REEL
    # -----------------------------------------

    post_payload = build_video_post_payload(channel)

    send_post(
        channel,
        post_payload
    )

    # -----------------------------------------
    # META STORIES
    # -----------------------------------------

    if service in ["instagram", "facebook"]:

        story_payload = build_story_payload(channel)

        send_post(
            channel,
            story_payload
        )

print("\n✅ VIDEO SCRIPT COMPLETED")
