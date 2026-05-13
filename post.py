import os
import random
import requests
from pathlib import Path

BUFFER_TOKEN = os.environ["BUFFER_ACCESS_TOKEN"]

# -----------------------------
# GraphQL helper
# -----------------------------
def graphql(query):
    response = requests.post(
        "https://api.buffer.com",
        json={"query": query},
        headers={
            "Authorization": f"Bearer {BUFFER_TOKEN}",
            "Content-Type": "application/json"
        }
    )

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)

    data = response.json()

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]

# -----------------------------
# Get organizations/channels
# -----------------------------
query = """
query {
  account {
    organizations {
      id
      name

      channels {
        id
        name
        service
      }
    }
  }
}
"""

data = graphql(query)

organization = data["account"]["organizations"][0]

print("Using organization:", organization["name"])

channels = organization["channels"]

print("Connected channels:")

for c in channels:
    print(c)

# -----------------------------
# Instagram channel
# -----------------------------
instagram_channel = next(
    c for c in channels if c["service"] == "instagram"
)

channel_id = instagram_channel["id"]

# -----------------------------
# Random caption
# -----------------------------
with open("captions.txt", "r", encoding="utf-8") as f:
    captions = [line.strip() for line in f if line.strip()]

caption = random.choice(captions)

# -----------------------------
# Random image
# -----------------------------
images = list(Path("images").glob("*"))

image = random.choice(images)

repo = os.environ["GITHUB_REPOSITORY"]

image_url = (
    f"https://raw.githubusercontent.com/"
    f"{repo}/main/images/{image.name}"
)

print("Selected image:", image.name)
print("Selected caption:", caption)

# -----------------------------
# CREATE POST
# -----------------------------
mutation = f'''
mutation {{
  createPost(
    input: {{
      channelId: "{channel_id}"
      text: "{caption}"
      schedulingType: automatic
      mode: shareNow

      assets: [
        {{
          sourceUrl: "{image_url}"
        }}
      ]
    }}
  ) {{

    ... on PostActionSuccess {{
      post {{
        id
        status
      }}
    }}

    ... on MutationError {{
      message
    }}
  }}
}}
'''

post_result = graphql(mutation)

print("POST RESULT:")
print(post_result)
