import os
import random
import requests
import json
from datetime import datetime, timedelta, timezone

# =========================================================
# CONFIG
# =========================================================

API_URL = "https://api.buffer.com/graphql"

IMAGE_FOLDER = "./images"
CAPTION_FILE = "captions.txt"

BASE_IMAGE_URL = (
    "https://raw.githubusercontent.com/"
    "enkisystems/enki-social-poster/main/images/"
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
        json={"query": query, "variables": variables or {}},
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
# GET ORG + CHANNELS (unchanged)
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
org_id = org_data["account"]["organizations"][0]["id"]

print("\n✅ Using organization:", org_data["account"]["organizations"][0]["name"])

channels_query = """
query ($orgId: OrganizationId!) {
  channels(input: { organizationId: $orgId }) {
    id
    name
    service
  }
}
"""

channels = graphql(channels_query, {"orgId": org_id})["channels"]

meta_channels = []
tiktok_channels = []

for c in channels:
    if c["service"].lower() in ["instagram", "facebook"]:
        meta_channels.append(c)
    elif c["service"].lower() == "tiktok":
        tiktok_channels.append(c)

print("\nTikTok:", len(tiktok_channels))
print("Meta:", len(meta_channels))

# =========================================================
# IMAGE + CAPTION
# =========================================================

all_images = [
    f for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
]

selected_image = random.choice(all_images)
IMAGE_URL = BASE_IMAGE_URL + selected_image

with open(CAPTION_FILE, "r", encoding="utf-8") as f:
    captions = [l.strip() for l in f if l.strip()]

selected_caption = random.choice(captions)

print("\n✅ Image:", selected_image)
print("✅ Caption:", selected_caption)

# =========================================================
# TIME (22:30 UTC target)
# =========================================================

now = datetime.now(timezone.utc)

scheduled = now.replace(hour=22, minute=30, second=0, microsecond=0)

if scheduled <= now:
    scheduled += timedelta(days=1)

scheduled += timedelta(minutes=random.randint(-24, 24))

scheduled_iso = scheduled.isoformat()

print("\n✅ Scheduled:", scheduled_iso)

# =========================================================
# FEED POST DAYS (NEW LOGIC)
# =========================================================

# Tuesday (2) + Friday (5)
feed_days = [2, 5]

is_feed_day = datetime.utcnow().isoweekday() in feed_days

print("\n📌 Feed post today?", is_feed_day)

# =========================================================
# GRAPHQL MUTATION
# =========================================================

mutation = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post { id text dueAt }
    }
    ... on MutationError {
      message
    }
  }
}
"""

# =========================================================
# META PAYLOAD
# =========================================================

def build_meta_payload(channel):

    service = channel["service"].lower()

    # STORY (always daily)
    if not is_feed_day:
        text = " "
    else:
        text = selected_caption

    payload = {
        "channelId": channel["id"],
        "text": text,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": scheduled_iso,
        "assets": [
            {
                "image": {
                    "url": IMAGE_URL
                }
            }
        ],
        "metadata": {
            service: {
                "type": "story" if not is_feed_day else "post",
                "shouldShareToFeed": True
            }
        }
    }

    return payload

# =========================================================
# TIKTOK (unchanged)
# =========================================================

def build_tiktok_payload(channel):
    return {
        "channelId": channel["id"],
        "text": selected_caption,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": scheduled_iso,
        "assets": [
            {"image": {"url": IMAGE_URL}}
        ]
    }

# =========================================================
# SEND
# =========================================================

def send(channel, builder):

    payload = builder(channel)

    print("\n===================================")
    print(f"🚀 Posting {channel['service']} ({channel['name']})")
    print(json.dumps(payload, indent=2))

    result = graphql(mutation, {"input": payload})

    print("\n✅ RESULT:")
    print(json.dumps(result, indent=2))

# =========================================================
# RUN META
# =========================================================

print("\n📘 META")
for c in meta_channels:
    send(c, build_meta_payload)

# =========================================================
# RUN TIKTOK
# =========================================================

print("\n🎵 TIKTOK")
for c in tiktok_channels:
    send(c, build_tiktok_payload)

print("\n✅ DONE")
