import random, re, os, json, requests, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
IG_USER_ID         = os.environ["IG_USER_ID"]
PAGE_TOKEN         = os.environ["FB_PAGE_ACCESS_TOKEN"]
FB_PAGE_ID         = os.environ["FB_PAGE_ID"]
FOLDER_ID          = "1iE-PeolUqqjGm_QjoSQvjMRTkzQe4v6X"
CAPTION_DOC_ID     = "12E55nTo05cP4CwllfuqNd63gTKEXxneu_UyV1r5efBU"
SHOPIFY_URL        = "https://enkisystems.com.au/products/gateguard"

# --- GOOGLE AUTH ---
creds = service_account.Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]),
    scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents"
    ]
)
drive = build("drive", "v3", credentials=creds)
docs  = build("docs",  "v1", credentials=creds)

# --- GET RANDOM IMAGE ---
print("Fetching images from Drive...")
results = drive.files().list(
    q=f"'{FOLDER_ID}' in parents and mimeType contains 'image/' and not name contains 'USED'",
    fields="files(id, name)",
    pageSize=100
).execute()
images = results.get("files", [])
if not images:
    raise Exception("No images found in folder")
chosen = random.choice(images)
print(f"Selected image: {chosen['name']}")

# Make image publicly accessible so Meta API can fetch it
drive.permissions().create(
    fileId=chosen["id"],
    body={"role": "reader", "type": "anyone"}
).execute()
image_url = f"https://drive.google.com/uc?export=download&id={chosen['id']}"

# --- GET NEXT UNUSED CAPTION ---
print("Fetching captions doc...")
doc = docs.documents().get(documentId=CAPTION_DOC_ID).execute()
full_text = ""
for elem in doc.get("body", {}).get("content", []):
    for pe in elem.get("paragraph", {}).get("elements", []):
        full_text += pe.get("textRun", {}).get("content", "")

captions = [c.strip() for c in re.split(r"={3,}", full_text) if c.strip()]
unused = [c for c in captions if not c.upper().startswith("USED")]

if not unused:
    raise Exception("All captions used — add more to the doc")

raw_caption = unused[0]
print(f"Caption: {raw_caption[:60]}...")

# Build final caption with hashtags and link
hashtags = "#dogsofinstagram #dogmom #dogsafety #gateguard #petowner #dogescape"
caption_ig = f"{raw_caption}\n\n{hashtags}\n\nShop: {SHOPIFY_URL}"

# --- POST TO INSTAGRAM STORY ---
print("Posting to Instagram...")
# Step 1: Create media container
r = requests.post(
    f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
    data={
        "image_url": image_url,
        "media_type": "STORIES",
        "access_token": PAGE_TOKEN
    }
)
r.raise_for_status()
container_id = r.json().get("id")
if not container_id:
    raise Exception(f"Failed to create IG container: {r.json()}")
print(f"Container created: {container_id}")

# Wait for container to be ready
time.sleep(5)

# Step 2: Publish Story
r = requests.post(
    f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
    data={
        "creation_id": container_id,
        "access_token": PAGE_TOKEN
    }
)
r.raise_for_status()
ig_post_id = r.json().get("id")
print(f"Instagram Story posted: {ig_post_id}")

# --- CROSS-POST TO FACEBOOK PAGE ---
print("Posting to Facebook...")
caption_fb = f"{raw_caption}\n\n{hashtags}"
r = requests.post(
    f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos",
    data={
        "url": image_url,
        "caption": caption_fb,
        "access_token": PAGE_TOKEN
    }
)
r.raise_for_status()
fb_post_id = r.json().get("id")
print(f"Facebook post published: {fb_post_id}")

# --- MARK CAPTION AS USED ---
print("Marking caption as used...")
docs.documents().batchUpdate(
    documentId=CAPTION_DOC_ID,
    body={"requests": [{
        "replaceAllText": {
            "containsText": {"text": raw_caption, "matchCase": True},
            "replaceText": f"USED: {raw_caption}"
        }
    }]}
).execute()

# Optionally revoke public access to image after posting
# drive.permissions().delete(fileId=chosen["id"], permissionId="anyoneWithLink").execute()

print(f"\n✅ Done. IG: {ig_post_id} | FB: {fb_post_id} | Caption: {raw_caption[:40]}...")
