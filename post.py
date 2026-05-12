import os
import random
import requests
from pathlib import Path

BUFFER_TOKEN = os.environ["BUFFER_ACCESS_TOKEN"]

# -----------------------------
# Buffer REST API helper
# -----------------------------
def buffer_get(url):
    return requests.get(url, params={
        "access_token": BUFFER_TOKEN
    }).json()

def buffer_post(url, data):
    data["access_token"] = BUFFER_TOKEN
    return requests.post(url, data=data).json()

# -----------------------------
# Get profiles (channels)
# -----------------------------
profiles = buffer_get("https://api.bufferapp.com/1/profiles.json")

print("Connected profiles:")
for p in profiles:
    print(p["id"], p["formatted_service"])

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
# GitHub raw image URL
# -----------------------------
repo = os.environ["GITHUB_REPOSITORY"]

image_url = f"https://raw.githubusercontent.com/{repo}/main/images/{image.name}"

print("Image:", image.name)
print("Caption:", caption)

# -----------------------------
# Create Buffer update
# -----------------------------
response = buffer_post(
    "https://api.bufferapp.com/1/updates/create.json",
    data={
        "text": caption,
        "profile_ids[]": profile_ids,
        "media[photo]": image_url
    }
)

print("Buffer response:")
print(response)
