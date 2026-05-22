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

org_data = graphql(org_query)
orgs = org_data["account"]["organizations"]

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

channels = graphql(channels_query, {"orgId": org_id})["channels"]

print("\n✅ Connected channels:")
for c in channels:
    print(c)

meta_channels = []
tiktok_channels = []

for c in channels:
    if c["service"].lower() in ["instagram", "facebook"]:
        meta_channels.append(c)
    elif c["service"].lower() == "tiktok":
        tiktok_channels.append(c)

# =========================================================
# IMAGE
# =========================================================

all_images = [
    f for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
]

selected_image = random.choice(all_images)
IMAGE_URL = BASE_IMAGE_URL + selected_image

# =========================================================
# CAPTIONS
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

scheduled = now.replace(hour=22, minute=0, second=0, microsecond=0)

if scheduled <= now:
    scheduled += timedelta(days=1)

scheduled += timedelta(minutes=random.randint(-24, 24))

scheduled_iso = scheduled.isoformat()

print("\n✅ Scheduled time UTC:", scheduled_iso)

# =========================================================
# STRATEGY
# =========================================================

today = datetime.now(timezone.utc).weekday()

POST_DAYS = [4]  # Thr -> Fri post 
is_post_day = today in POST_DAYS

print("\n📌 Caption mode:")
print("Full caption day?", is_post_day)

# =========================================================
# MUTATION
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
        "text": selected_caption if is_post_day else "",
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

    # =====================================================
    # INSTAGRAM (FIXED)
    # =====================================================

    if service == "instagram":
        payload["metadata"]["instagram"] = {
            "type": "post" if is_post_day else "story",
            "shouldShareToFeed": True   # REQUIRED by Buffer schema
        }

    # =====================================================
    # FACEBOOK
    # =====================================================

    elif service == "facebook":
        payload["metadata"]["facebook"] = {
            "type": "post" if is_post_day else "story"
        }

    return payload

# =========================================================
# TIKTOK PAYLOAD
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

def send_post(channel, builder):

    payload = builder(channel)

    print("\n===================================")
    print(f"🚀 Posting {channel['service']} ({channel['name']})")
    print(json.dumps(payload, indent=2))

    try:
        result = graphql(mutation, {"input": payload})

        post = result.get("createPost", {})

        if "message" in post:
            print("\n❌ BUFFER ERROR:")
            print(post["message"])
        else:
            print("\n✅ POST SUCCESS")
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"\n❌ FAILED on {channel['service']}")
        print(e)

# =========================================================
# RUN META
# =========================================================

print("\n===================================")
print("📘 POSTING TO META CHANNELS")
print("===================================")

for c in meta_channels:
    try:
        send_post(c, build_meta_payload)
    except Exception as e:
        print(f"❌ META FAILED {c['service']}: {e}")

# =========================================================
# RUN TIKTOK
# =========================================================

print("\n===================================")
print("🎵 POSTING TO TIKTOK CHANNELS")
print("===================================")

for c in tiktok_channels:
    try:
        send_post(c, build_tiktok_payload)
    except Exception as e:
        print(f"❌ TIKTOK FAILED {c['service']}: {e}")

print("\n✅ SCRIPT COMPLETED")
