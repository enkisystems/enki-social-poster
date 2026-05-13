import os
import random
import requests
from pathlib import Path

BUFFER_TOKEN = os.environ["BUFFER_ACCESS_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]

# -----------------------------
# GraphQL helper
# -----------------------------
def graphql(query, variables=None):
    r = requests.post(
        "https://api.buffer.com",
        json={"query": query, "variables": variables or {}},
        headers={
            "Authorization": f"Bearer {BUFFER_TOKEN}",
            "Content-Type": "application/json"
        }
    )

    print("STATUS:", r.status_code)
    print("RESPONSE:", r.text)

    data = r.json()

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]


# -----------------------------
# Get organization
# -----------------------------
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


# -----------------------------
# Get channels (DOC-CORRECT)
# -----------------------------
channels_query = """
query GetChannels($orgId: ID!) {
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


# -----------------------------
# Load caption
# -----------------------------
with open("captions.txt", "r", encoding="utf-8") as f:
    captions = [l.strip() for l in f if l.strip()]

caption = random.choice(captions)


# -----------------------------
# Load image
# -----------------------------
images = list(Path("images").glob("*"))
image = random.choice(images)

image_url = f"https://raw.githubusercontent.com/{REPO}/main/images/{image.name}"

print("\nSelected image:", image.name)
print("Selected caption:", caption)
print("Image URL:", image_url)


# -----------------------------
# Create post mutation (DOC EXACT)
# -----------------------------
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


# -----------------------------
# Post each channel
# -----------------------------
for channel in channels:
    service = channel["service"]

    print(f"\nPosting to {service}...")

    input_data = {
        "channelId": channel["id"],
        "text": caption,
        "schedulingType": "automatic",
        "mode": "addToQueue",
        "assets": [
            {
                "image": {
                    "url": image_url
                }
            }
        ]
    }

    # IMPORTANT: only Instagram needs this
    if service == "instagram":
        input_data["channelData"] = {
            "instagram": {
                "postType": "post"
            }
        }

    result = graphql(mutation, {"input": input_data})

    print("\nPOST RESULT:")
    print(result)
