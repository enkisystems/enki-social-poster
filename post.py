import os
import random
import requests
from pathlib import Path

BUFFER_TOKEN = os.environ["BUFFER_ACCESS_TOKEN"]

# -------------------------------------------------
# GraphQL helper
# -------------------------------------------------
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

# -------------------------------------------------
# Get organizations
# -------------------------------------------------
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

organization = organizations[0]

print("Using organization:", organization["name"])

# -------------------------------------------------
# Get channels
# -------------------------------------------------
channels_query = """
query GetChannels($orgId: OrganizationId!) {
  channels(input: { organizationId: $orgId }) {
    id
    name
    service
  }
}
"""

channels_data = graphql(
    channels_query,
    {
        "orgId": organization["id"]
    }
)

channels = channels_data["channels"]

if not channels:
    raise Exception("No channels found")

print("Connected channels:")

for c in channels:
    print(c)

# -------------------------------------------------
# Pick caption
# -------------------------------------------------
with open("captions.txt", "r", encoding="utf-8") as f:
    captions = [line.strip() for line in f if line.strip()]

if not captions:
    raise Exception("No captions found")

caption = random.choice(captions)

# -------------------------------------------------
# Pick image
# -------------------------------------------------
images = list(Path("images").glob("*"))

if not images:
    raise Exception("No images found")

image = random.choice(images)

print("Selected image:", image.name)
print("Selected caption:", caption)

# -------------------------------------------------
# GitHub raw image URL
# -------------------------------------------------
repo = os.environ["GITHUB_REPOSITORY"]

image_url = (
    f"https://raw.githubusercontent.com/"
    f"{repo}/main/images/{image.name}"
)

print("Image URL:", image_url)

# -------------------------------------------------
# Inspect AssetInput fields
# -------------------------------------------------
mutation = """
query {
  __type(name: "AssetInput") {
    inputFields {
      name
      type {
        name
        kind
        ofType {
          name
          kind
        }
      }
    }
  }
}
"""

result = graphql(mutation)

print("ASSET INPUT SCHEMA:")
print(result)

# -------------------------------------------------
# Post to each channel
# -------------------------------------------------
for channel in channels:

    print(f"Posting to {channel['service']}...")

    variables = {
        "input": {
            "channelId": channel["id"],

            "text": caption,

            "schedulingType": "automatic",

            "mode": "shareNow",

            "assets": [
                {
                    "source": image_url
                }
            ]
        }
    }

    result = graphql(mutation, variables)

    print("POST RESULT:")
    print(result)
