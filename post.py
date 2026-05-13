import os
import requests
import random
import sys

API_URL = "https://api.buffer.com"


# -------------------------
# FIXED ENV HANDLING (IMPORTANT)
# -------------------------
API_KEY = (
    os.getenv("BUFFER_API_KEY")
    or os.getenv("BUFFER_ACCESS_TOKEN")
)

if not API_KEY:
    print("\n❌ Missing Buffer API key")
    print("Looked for: BUFFER_API_KEY OR BUFFER_ACCESS_TOKEN")
    print("\nAvailable env vars containing 'BUFFER':")
    print([k for k in os.environ.keys() if "BUFFER" in k])
    sys.exit(1)


# -------------------------
# GRAPHQL HELPER
# -------------------------
def graphql(query, variables=None):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "variables": variables or {}
    }

    res = requests.post(API_URL, json=payload, headers=headers)

    print("\nSTATUS:", res.status_code)

    data = res.json()
    print("RESPONSE:", data)

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]


# -------------------------
# GET ORGANIZATION
# -------------------------
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
org = org_data["account"]["organizations"][0]
org_id = org["id"]

print("\nUsing organization:", org["name"])


# -------------------------
# GET CHANNELS
# -------------------------
channels_query = """
query GetChannels($orgId: OrganizationId!) {
  channels(input: { organizationId: $orgId }) {
    id
    name
    service
  }
}
"""

channels_data = graphql(channels_query, {"orgId": org_id})
channels = channels_data["channels"]

print("\nConnected channels:")
for c in channels:
    print(c)


def get_channel(service):
    return next((c for c in channels if c["service"] == service), None)


instagram = get_channel("instagram")
facebook = get_channel("facebook")
tiktok = get_channel("tiktok")


# -------------------------
# RANDOM IMAGES (LOCAL FOLDER)
# -------------------------
images = [
    f for f in os.listdir("images")
    if f.endswith(".png")
]

image_file = random.choice(images)


# -------------------------
# RANDOM CAPTIONS
# -------------------------
captions = [
    "Because accidents happen fast. GateGuard alerts you the moment a gate opens.",
    "Know the moment your gate is opened.",
    "Smart gate alerts for families and pet owners.",
    "Peace of mind when it matters most — instant gate alerts.",
    "Never wonder if the gate was left open again.",
    "Because fur babies are family too — stay alerted instantly.",
    "Real-time gate alerts straight to your phone and watch.",
]

caption = random.choice(captions)


# -------------------------
# IMAGE URL (GITHUB RAW)
# -------------------------
image_url = (
    "https://raw.githubusercontent.com/enkisystems/enki-social-poster/main/images/"
    + image_file
)

print("\nSelected image:", image_file)
print("Selected caption:", caption)
print("Image URL:", image_url)


# -------------------------
# BUFFER ASSETS (CORRECT FORMAT)
# -------------------------
assets = [
    {
        "image": {
            "url": image_url
        }
    }
]


# -------------------------
# MUTATION
# -------------------------
mutation = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post {
        id
        text
        status
        dueAt
      }
    }
    ... on MutationError {
      message
    }
  }
}
"""


def create_post(channel):
    if not channel:
        print("\n⚠️ Skipping missing channel")
        return

    print(f"\nPosting to {channel['service']}...")

    input_data = {
        "text": caption,
        "channelId": channel["id"],
        "schedulingType": "automatic",
        "mode": "addToQueue",
        "assets": assets
    }

    result = graphql(mutation, {"input": input_data})

    print("\nPOST RESULT:")
    print(result)


# -------------------------
# RUN
# -------------------------
create_post(instagram)
create_post(facebook)
create_post(tiktok)
