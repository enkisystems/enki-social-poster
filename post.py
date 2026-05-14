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
# SPLIT CHANNELS
# =========================================================

meta_channels = []
tiktok_channels = []

for channel in channels:

    service = channel["service"].lower()

    if service in ["instagram", "facebook"]:
        meta_channels.append(channel)

    elif service == "tiktok":
        tiktok_channels.append(channel)

print("\nTikTok channels:", len(tiktok_channels))
print("Meta channels:", len(meta_channels))

# =========================================================
# RANDOM IMAGE
# =========================================================

all_images = [
    file for file in os.listdir(IMAGE_FOLDER)
    if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
]

if not all_images:
    raise Exception("No images found")

selected_image = random.choice(all_images)

IMAGE_URL = BASE_IMAGE_URL + selected_image

# =========================================================
# CAPTIONS
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

# =========================================================
# CAPTION STRATEGY (NEW)
# =========================================================
# 5 out of 7 days → story-style (no selling caption)
# 2 out of 7 days → full caption feed post

today_seed = datetime.utcnow().isoweekday()  # 1–7 stable daily pattern
is_caption_day = today_seed in [3, 6]  # tweak anytime

if is_caption_day:
    meta_caption = selected_caption
else:
    meta_caption = " "

print("\n📌 Caption mode:")
print("Full caption day?" , is_caption_day)

print("\n✅ Selected image:", selected_image)
print("✅ Caption (Meta):", meta_caption)
print("✅ Image URL:", IMAGE_URL)

# =========================================================
# SCHEDULE TIME (22:30 UTC target)
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

scheduled += timedelta(
    minutes=random.randint(-24, 24)
)

scheduled_iso = scheduled.isoformat()

print("\n✅ Scheduled time UTC:", scheduled_iso)

# =========================================================
# GRAPHQL MUTATION
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
# META PAYLOAD
# =========================================================

def build_meta_payload(channel):

    service = channel["service"].lower()

    payload = {
        "channelId": channel["id"],
        "text": meta_caption,
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
        "metadata": {}
    }

    if service == "instagram":
        payload["metadata"]["instagram"] = {
            "type": "story",
            "shouldShareToFeed": True
        }

    elif service == "facebook":
        payload["metadata"]["facebook"] = {
            "type": "story"
        }

    return payload

# =========================================================
# TIKTOK PAYLOAD (ALWAYS CAPTIONED)
# =========================================================

def build_tiktok_payload(channel):

    return {
        "channelId": channel["id"],
        "text": selected_caption,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": scheduled_iso,
        "assets": [
            {
                "image": {
                    "url": IMAGE_URL
                }
            }
        ]
    }

# =========================================================
# SEND POST
# =========================================================

def send_post(channel, payload_builder):

    payload = payload_builder(channel)

    print("\n===================================")
    print(f"🚀 Posting to {channel['service']} ({channel['name']})")

    print("\nPAYLOAD:")
    print(json.dumps(payload, indent=2))

    result = graphql(mutation, {"input": payload})

    create_post = result.get("createPost", {})

    if "message" in create_post:
        print("\n❌ BUFFER ERROR:")
        print(create_post["message"])
    else:
        print("\n✅ POST SUCCESS")
        print(json.dumps(result, indent=2))

# =========================================================
# POST TO META
# =========================================================

print("\n===================================")
print("📘 POSTING TO META CHANNELS")
print("===================================")

for channel in meta_channels:
    send_post(channel, build_meta_payload)

# =========================================================
# POST TO TIKTOK
# =========================================================

print("\n===================================")
print("🎵 POSTING TO TIKTOK CHANNELS")
print("===================================")

for channel in tiktok_channels:
    send_post(channel, build_tiktok_payload)

print("\n✅ SCRIPT COMPLETED")
