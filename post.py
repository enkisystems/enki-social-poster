import os
import random
import requests
from pathlib import Path

BUFFER_TOKEN = os.environ["BUFFER_ACCESS_TOKEN"]

PROFILE_IDS = [
    os.environ["BUFFER_INSTAGRAM_ID"],
    os.environ["BUFFER_FACEBOOK_ID"],
    os.environ["BUFFER_TIKTOK_ID"]
]

# Load captions
with open("captions.txt", "r", encoding="utf-8") as f:
    captions = [line.strip() for line in f if line.strip()]

caption = random.choice(captions)

# Pick random image
images = list(Path("images").glob("*"))
image = random.choice(images)

# Build GitHub raw image URL
repo = os.environ["GITHUB_REPOSITORY"]
branch = "main"

image_url = f"https://raw.githubusercontent.com/{repo}/{branch}/images/{image.name}"

print("Selected image:", image.name)
print("Selected caption:", caption)

# Send to Buffer
url = "https://api.bufferapp.com/1/updates/create.json"

data = {
    "access_token": BUFFER_TOKEN,
    "text": caption,
    "profile_ids[]": PROFILE_IDS,
    "media[photo]": image_url
}

response = requests.post(url, data=data)

print(response.status_code)
print(response.text)
