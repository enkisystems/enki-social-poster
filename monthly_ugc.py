import os
import random
import requests
import json
from datetime import datetime, timedelta, timezone

# =========================================================
# CONFIG
# =========================================================

API_URL = "https://api.buffer.com/graphql"

VIDEO_FOLDER = "./ugc_videos"
CAPTION_FILE = "captions.txt"

BASE_VIDEO_URL = (
    "https://raw.githubusercontent.com/"
    "enkisystems/enki-social-poster/main/ugc_videos/"
)

# =========================================================
# AUTH
# =========================================================

TOKEN = os.getenv("BUFFER_ACCESS_TOKEN") or os.getenv("BUFFER_API_KEY")

if not TOKEN:
    print("\n❌ ERROR: Missing BUFFER_ACCESS_TOKEN")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# =========================================================
# GRAPHQL
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

    data = response.json()

    print(json.dumps(data, indent=2))

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]

# =========================================================
# GET ORG
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

orgs = graphql(org_query)["account"]["organizations"]

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

channels = graphql(
    channels_query,
    {"orgId": org_id}
)["channels"]

supported_channels = []

for c in channels:

    if c["service"].lower() in [
        "instagram",
        "facebook",
        "tiktok"
    ]:
        supported_channels.append(c)

# =========================================================
# RANDOM VIDEO
# =========================================================

all_videos = [
    f for f in os.listdir(VIDEO_FOLDER)
    if f.lower().endswith((".mp4", ".mov", ".m4v"))
]

if not all_videos:
    raise Exception("No UGC videos found")

selected_video = random.choice(all_videos)

VIDEO_URL = BASE_VIDEO_URL + selected_video

print("\n✅ Selected UGC:", selected_video)

# =========================================================
# RANDOM CAPTION
# =========================================================

with open(CAPTION_FILE, "r", encoding="utf-8") as f:

    captions = [
        line.strip()
        for line in f
        if line.strip() and line.strip() != "========="
    ]

selected_caption = random.choice(captions)

# =========================================================
# SCHEDULE TIME
# =========================================================

now = datetime.now(timezone.utc)

scheduled = now.replace(
    hour=22,
    minute=0,
    second=0,
    microsecond=0
)

scheduled += timedelta(minutes=random.randint(-20, 20))

scheduled += timedelta(
    minutes=random.randint(-20, 20)
)

scheduled_iso = scheduled.isoformat()

print("\n✅ Scheduled UTC:", scheduled_iso)

# =========================================================
# MUTATION
# =========================================================

mutation = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {

    ... on PostActionSuccess {
      post {
        id
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
# SEND
# =========================================================

def send_post(channel, payload):

    print("\n===================================")
    print(f"🚀 Posting {channel['service']}")
    print(json.dumps(payload, indent=2))

    try:

        result = graphql(
            mutation,
            {"input": payload}
        )

        post = result.get("createPost", {})

        if "message" in post:

            print("\n❌ BUFFER ERROR:")
            print(post["message"])

        else:

            print("\n✅ SUCCESS")
            print(json.dumps(result, indent=2))

    except Exception as e:

        print("\n❌ FAILED")
        print(e)

# =========================================================
# BUILD PAYLOAD
# =========================================================

def build_payload(channel):

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

    # INSTAGRAM REEL

    if service == "instagram":

        payload["metadata"] = {
            "instagram": {
                "type": "reel",
                "shouldShareToFeed": True
            }
        }

    # FACEBOOK REEL

    elif service == "facebook":

        payload["metadata"] = {
            "facebook": {
                "type": "reel"
            }
        }

    return payload

# =========================================================
# RUN
# =========================================================

print("\n===================================")
print("🎬 POSTING MONTHLY UGC")
print("===================================")

for c in supported_channels:

    send_post(
        c,
        build_payload(c)
    )

print("\n✅ DONE")
