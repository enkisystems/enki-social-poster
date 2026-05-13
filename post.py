import os
import random
import requests
from pathlib import Path

BUFFER_TOKEN = os.environ["BUFFER_ACCESS_TOKEN"]

# -----------------------------
# Buffer API helpers
# -----------------------------
def buffer_get(url):
    response = requests.get(
        url,
        params={
            "access_token": BUFFER_TOKEN
        }
    )

    print("GET STATUS:", response.status_code)
    print("GET RESPONSE:", response.text)

    response.raise_for_status()

    return response.json()

def buffer_post(url, data):
    data["access_token"] = BUFFER_TOKEN

    response = requests.post(url, data=data)

    print("POST STATUS:", response.status_code)
    print("POST RESPONSE:", response.text)

    response.raise_for_status()

    return response.json()

# -----------------------------
# Get profiles
# -----------------------------
profiles = buffer_get(
    "https://api.bufferapp.com/1/profiles.json"
)

# Safety validation
if not isinstance(profiles, list):
    raise Exception(f"Unexpected profiles response: {profiles}")

print("Connected profiles:")

for p in profiles:
    print(p)

profile_ids = [p["id"] for p in profiles]

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
# GitHub image URL
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
response = buffer_post(
    "https://api.bufferapp.com/1/updates/create.json",
    {
        "text": caption,
        "profile_ids[]": profile_ids,
        "media[photo]": image_url
    }
)

print("Final response:")
print(response)
