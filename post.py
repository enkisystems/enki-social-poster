import os
import random
import requests

API_URL = "https://api.buffer.com/graphql"

# ----------------------------
# AUTH
# ----------------------------
TOKEN = os.getenv("BUFFER_ACCESS_TOKEN") or os.getenv("BUFFER_API_KEY")

if not TOKEN:
    print("\n❌ ERROR: Missing BUFFER_ACCESS_TOKEN / BUFFER_API_KEY")
    print("\nAvailable environment variables:")
    print(list(os.environ.keys()))
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# ----------------------------
# GRAPHQL HELPER
# ----------------------------
def graphql(query, variables=None):
    response = requests.post(
        API_URL,
        json={
            "query": query,
            "variables": variables or {}
        },
        headers=HEADERS
    )

    data = response.json()

    print("\nSTATUS:", response.status_code)
    print("RESPONSE:", data)

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]

# ----------------------------
# GET ORGANIZATION
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

org_data = graphql(org_query)

orgs = org_data["account"]["organizations"]

if not orgs:
    raise Exception("No organizations found")

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

channels_data = graphql(
    channels_query,
    {"orgId": org_id}
)

channels = channels_data["channels"]

print("\nConnected channels:")

for channel in channels:
    print(channel)

# ----------------------------
# RANDOM IMAGE
# ----------------------------
IMAGE_FOLDER = "./images"

all_images = [
    file for file in os.listdir(IMAGE_FOLDER)
    if file.lower().endswith((
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    ))
]

if not all_images:
    raise Exception("No images found in ./images")

selected_image = random.choice(all_images)

IMAGE_URL = (
    "https://raw.githubusercontent.com/"
    "enkisystems/enki-social-poster/main/images/"
    + selected_image
)

# ----------------------------
# RANDOM CAPTION
# ----------------------------
CAPTION_FILE = "captions.txt"

with open(CAPTION_FILE, "r", encoding="utf-8") as file:
    captions = [
        line.strip()
        for line in file.readlines()
        if line.strip() and line.strip() != "========="
    ]

if not captions:
    raise Exception("No captions found")

selected_caption = random.choice(captions)

print("\nSelected image:", selected_image)
print("Selected caption:", selected_caption)
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
# BUILD PAYLOAD
# ----------------------------
def build_payload(channel):

    payload = {
        "channelId": channel["id"],
        "text": selected_caption,
        "schedulingType": "automatic",
        "mode": "addToQueue"
    }

    # Add image asset
    payload["assets"] = [
        {
            "image": {
                "url": IMAGE_URL
            }
        }
    ]

    return payload

# ----------------------------
# SEND POST
# ----------------------------
def send_post(channel):

    payload = build_payload(channel)

    print(
        f"\nPosting to "
        f"{channel['service']} "
        f"({channel['name']})..."
    )

    try:

        result = graphql(
            mutation,
            {"input": payload}
        )

        print("\nPOST RESULT:")
        print(result)

    except Exception as error:

        print(f"\n❌ FAILED on {channel['service']}")
        print(error)

        # ---------------------------------
        # FALLBACK: TRY TEXT ONLY
        # ---------------------------------
        fallback_payload = {
            "channelId": channel["id"],
            "text": selected_caption,
            "schedulingType": "automatic",
            "mode": "addToQueue"
        }

        print("\n🔁 Retrying text-only fallback...")

        try:

            fallback_result = graphql(
                mutation,
                {"input": fallback_payload}
            )

            print("\nFALLBACK SUCCESS:")
            print(fallback_result)

        except Exception as fallback_error:

            print("\n❌ FALLBACK FAILED")
            print(fallback_error)

# ----------------------------
# RUN
# ----------------------------
for channel in channels:
    send_post(channel)

print("\n✅ Script completed")
