import os
import random
import requests

API_URL = "https://api.buffer.com/graphql"

# ----------------------------
# AUTH
# ----------------------------
TOKEN = os.getenv("BUFFER_ACCESS_TOKEN") or os.getenv("BUFFER_API_KEY")

if not TOKEN:
    print("❌ ERROR: Missing BUFFER_ACCESS_TOKEN / BUFFER_API_KEY")
    print("Available env vars:", list(os.environ.keys()))
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# ----------------------------
# GRAPHQL HELPER
# ----------------------------
def graphql(query, variables=None):
    res = requests.post(
        API_URL,
        json={"query": query, "variables": variables or {}},
        headers=HEADERS
    )
    data = res.json()

    print("STATUS:", res.status_code)
    print("RESPONSE:", data)

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]

# ----------------------------
# GET ORG
# ----------------------------
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

orgs = graphql(org_query)["account"]["organizations"]
org_id = orgs[0]["id"]

print("\nUsing organization:", orgs[0]["name"])

# ----------------------------
# GET CHANNELS
# ----------------------------
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

print("\nConnected channels:")
for c in channels:
    print(c)

# ----------------------------
# RANDOM IMAGE FROM FOLDER
# ----------------------------
IMAGE_FOLDER = "./images"

images = [
    os.path.join(IMAGE_FOLDER, f)
    for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
]

if not images:
    raise Exception("No images found in ./images folder")

image_path = random.choice(images)

# GitHub raw pattern (adjust if needed)
IMAGE_URL = (
    "https://raw.githubusercontent.com/enkisystems/enki-social-poster/main/"
    + image_path.replace("\\", "/")
)

# ----------------------------
# RANDOM CAPTION
# ----------------------------
CAPTION_FILE = "captions.txt"

with open(CAPTION_FILE, "r", encoding="utf-8") as f:
    captions = [line.strip() for line in f if line.strip()]

if not captions:
    raise Exception("No captions found in captions.txt")

caption = random.choice(captions)

print("\nSelected image:", os.path.basename(image_path))
print("Selected caption:", caption)
print("Image URL:", IMAGE_URL)

# ----------------------------
# CREATE POST MUTATION
# ----------------------------
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

# ----------------------------
# POST EACH CHANNEL SAFELY
# ----------------------------
def send_post(channel):
    payload = {
        "channelId": channel["id"],
        "text": caption,
        "schedulingType": "automatic",
        "mode": "addToQueue",
        "assets": [
            {
                "image": {
                    "url": IMAGE_URL
                }
            }
        ]
    }

    print(f"\nPosting to {channel['service']} ({channel['name']})...")

    try:
        result = graphql(mutation, {"input": payload})
        print("\nPOST RESULT:")
        print(result)
    except Exception as e:
        print(f"\n❌ FAILED on {channel['service']}")
        print(e)


for channel in channels:
    send_post(channel)
