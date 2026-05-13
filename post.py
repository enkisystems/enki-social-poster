import os
import random
import requests
from pathlib import Path

BUFFER_TOKEN = os.environ["BUFFER_ACCESS_TOKEN"]

# -----------------------------
# GraphQL helper
# -----------------------------
def graphql(query, variables=None):

    response = requests.post(
        "https://api.buffer.com",
        json={
            "query": query,
            "variables": variables or {}
        },
        headers={
            "Authorization": f"Bearer {BUFFER_TOKEN}",
            "Content-Type": "application/json"
        }
    )

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)

    data = response.json()

    # GraphQL errors
    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]


# -----------------------------
# Get organization
# -----------------------------
org_query = """
query GetOrganizations {
  account {
    organizations {
      id
      name
    }
  }
}
"""

org_data = graphql(org_query)

organizations = org_data["account"]["organizations"]

if not organizations:
    raise Exception("No organizations found")

organization_id = organizations[0]["id"]

print("Using organization:", organizations[0]["name"])


# -----------------------------
# Get channels
# -----------------------------
channels_query = """
query GetChannels($organizationId: OrganizationId!) {
  channels(input: { organizationId: $organizationId }) {
    id
    name
    service
  }
}
"""

channels_data = graphql(
    channels_query,
    {
        "organizationId": organization_id
    }
)

channels = channels_data["channels"]

if not channels:
    raise Exception("No channels found")

print("\nConnected channels:")

for c in channels:
    print(c)


# -----------------------------
# Load captions
# -----------------------------
with open("captions.txt", "r", encoding="utf-8") as f:
    captions = [line.strip() for line in f if line.strip()]

if not captions:
    raise Exception("No captions found")

caption = random.choice(captions)


# -----------------------------
# Load images
# -----------------------------
images = list(Path("images").glob("*"))

if not images:
    raise Exception("No images found")

image = random.choice(images)


# -----------------------------
# GitHub raw image URL
# -----------------------------
repo = os.environ["GITHUB_REPOSITORY"]

image_url = (
    f"https://raw.githubusercontent.com/"
    f"{repo}/main/images/{image.name}"
)

print("\nSelected image:", image.name)
print("Selected caption:", caption)
print("Image URL:", image_url)


# -----------------------------
# Create post mutation
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
# Post to ALL channels
# -----------------------------
for channel in channels:

    print(f"\nPosting to {channel['service']}...")

    variables = {
        "input": {

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
    }

    result = graphql(mutation, variables)

    print("\nPOST RESULT:")
    print(result)
