import os
import requests
import random

API_URL = "https://api.buffer.com"
API_KEY = os.environ.get("BUFFER_API_KEY")

if not API_KEY:
    raise Exception("Missing BUFFER_API_KEY env variable")


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

    print("STATUS:", res.status_code)
    data = res.json()
    print("RESPONSE:", data)

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]


# -------------------------
# 1. Get organization
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
# 2. Get channels
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

# pick channels by service
def pick(service):
    for c in channels:
        if c["service"] == service:
            return c
    return None


instagram = pick("instagram")
facebook = pick("facebook")
tiktok = pick("tiktok")


# -------------------------
# 3. Pick image + caption
# -------------------------
images = [
    "Flux2-Klein_00007_.png",
    "Flux2-Klein_00066_.png",
    "Flux2-Klein_00069_.png",
    "Flux2-Klein_00060_.png",
]

image_file = random.choice(images)

caption = "Because accidents happen fast. GateGuard alerts you the moment a gate opens."

image_url = f"https://raw.githubusercontent.com/enkisystems/enki-social-poster/main/images/{image_file}"

print("\nSelected image:", image_file)
print("Selected caption:", caption)
print("Image URL:", image_url)


# -------------------------
# 4. Correct asset format (IMPORTANT FIX)
# -------------------------
assets = [
    {
        "image": {
            "url": image_url
        }
    }
]


# -------------------------
# 5. Create post mutation (CORRECT SHAPE)
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
# 6. POST (IMPORTANT FIX: no Instagram/Facebook type fields)
# -------------------------
create_post(instagram)
create_post(facebook)
create_post(tiktok)
