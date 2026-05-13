import os
import requests
import random
import sys

API_URL = "https://api.buffer.com"

# -------------------------
# ENV SAFETY CHECK
# -------------------------
API_KEY = os.getenv("BUFFER_API_KEY")

if not API_KEY:
    print("\n❌ ERROR: Missing BUFFER_API_KEY environment variable\n")
    print("Available environment variables:")
    print(list(os.environ.keys()))
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

    try:
        data = res.json()
    except Exception:
        print("RAW RESPONSE:", res.text)
        raise

    print("RESPONSE:", data)

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]


# -------------------------
# 1. GET ORGANIZATION
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
# 2. GET CHANNELS
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
# 3. CONTENT
# -------------------------
images = [
    "Flux2-Klein_00007_.png",
    "Flux2-Klein_00060_.png",
    "Flux2-Klein_00066_.png",
    "Flux2-Klein_00069_.png",
    "Flux2-Klein_00182_.png",
]

image_file = random.choice(images)

caption = "Because accidents happen fast. GateGuard alerts you the moment a gate opens."

image_url = (
    "https://raw.githubusercontent.com/enkisystems/enki-social-poster/main/images/"
    + image_file
)

print("\nSelected image:", image_file)
print("Selected caption:", caption)
print("Image URL:", image_url)


# -------------------------
# 4. CORRECT BUFFER ASSET FORMAT
# -------------------------
assets = [
    {
        "image": {
            "url": image_url
        }
    }
]


# -------------------------
# 5. MUTATION (CORRECT)
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
# 6. POST LOGIC
# -------------------------
create_post(instagram)
create_post(facebook)
create_post(tiktok)
