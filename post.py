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

    response.raise_for_status()

    data = response.json()

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
query GetChannels($organizationId: ID!) {
  organization(id: $organizationId) {
    channels {
      id
      name
      service
    }
  }
}
"""

channels_data = graphql(
    channels_query,
    {
        "organizationId": organization_id
    }
)

channels = channels_data["organization"]["channels"]

if not channels:
    raise Exception("No channels found")

print("Connected channels:")

for c in channels:
    print(c)

channel_ids = [c["id"] for c in channels]

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

print("Selected image:", image.name)
print("Selected caption:", caption)

# -----------------------------
# Create post
# -----------------------------
mutation = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on Post {
      id
      status
    }

    ... on MutationError {
      message
    }
  }
}
"""

variables = {
    "input": {
        "channelIds": channel_ids,
        "content": {
            "text": caption,
            "media": [
                {
                    "url": image_url
                }
            ]
        }
    }
}

post_result = graphql(mutation, variables)

print("POST RESULT:")
print(post_result)
