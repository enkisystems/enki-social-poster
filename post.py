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

    response.raise_for_status()
    return response.json()

# -----------------------------
# Get channels
# -----------------------------
query = """
query {
  channels {
    id
    service
    name
  }
}
"""

result = graphql(query)

channels = result["data"]["channels"]

print("Connected channels:")
for c in channels:
    print(c)

# -----------------------------
# Pick random caption
# -----------------------------
with open("captions.txt", "r", encoding="utf-8") as f:
    captions = [line.strip() for line in f if line.strip()]

caption = random.choice(captions)

# -----------------------------
# Pick random image
# -----------------------------
images = list(Path("images").glob("*"))
image = random.choice(images)

# -----------------------------
# GitHub raw image URL
# -----------------------------
repo = os.environ["GITHUB_REPOSITORY"]

image_url = f"https://raw.githubusercontent.com/{repo}/main/images/{image.name}"

print("Selected image:", image.name)
print("Selected caption:", caption)

# -----------------------------
# Channel IDs
# -----------------------------
channel_ids = [c["id"] for c in channels]

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

print(post_result)
