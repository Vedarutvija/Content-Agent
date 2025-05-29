import os
import requests
import json
from dotenv import load_dotenv
from typing import Optional
from bs4 import BeautifulSoup
# LangChain imports
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.schema import Document
import openai
# Social media APIs
import tweepy

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_TOKEN")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_ORGANIZATION_ID = os.getenv("LINKEDIN_ORGANIZATION_ID")
TWITTER_BEARER_TOKEN= os.getenv("TWITTER_BEARER_TOKEN")

# Helper: Retrieve web content and build retriever 

def build_retriever(url: str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract visible text from the page
    text = soup.get_text(separator="\n", strip=True)

    # Avoid large token count
    if len(text) > 500_000:
        text = text[:500_000]  # truncate to prevent embedding overflow

    doc = Document(page_content=text, metadata={"source": url})
    docs = [doc]

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splitted_docs = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(splitted_docs, embeddings)

    return vectorstore.as_retriever(search_kwargs={"k": 3})

# Generate caption using LangChain RAG pipeline
def generate_caption(topic: str, retriever):
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a social media expert. Use the following context to write a short, engaging caption for a post about "{question}" on Instagram/Facebook/Twitter/LinkedIn:

Context:
{context}

Caption:
"""
    )
    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-4"),
        retriever=retriever,
        chain_type="stuff",  # <-- change here
        chain_type_kwargs={"prompt": prompt_template},
        return_source_documents=False
    )
    return qa.run(topic)

#Image Generation
def generate_image(prompt: str) -> str:
    try:
        response = openai.images.generate(
            model="dall-e-3",  # Use "dall-e-2" if you don't have access to 3
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url
        print(f"✅ AI image generated: {image_url}")
        return image_url
    except Exception as e:
        print(f"❌ Failed to generate image: {e}")
        return None
# Post to Facebook using Graph API manually
def post_to_facebook(caption: str, image_url: Optional[str] = None):
    try:
        if image_url:
            image_data = requests.get(image_url).content
            files = {
                'source': ('image.jpg', image_data, 'image/jpeg')
            }
            payload = {
                'caption': caption,
                'access_token': FACEBOOK_PAGE_TOKEN
            }
            res = requests.post(
                f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos",
                data=payload,
                files=files
            )
        else:
            payload = {
                'message': caption,
                'access_token': FACEBOOK_PAGE_TOKEN
            }
            res = requests.post(
                f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed",
                data=payload
            )

        res.raise_for_status()
        print("Facebook post successful!")
    except Exception as e:
        print("Facebook post failed:", e)
        print("Response:", res.text if 'res' in locals() else 'No response')

# Post to Instagram (must be image post)
def post_to_instagram(caption: str, image_url: str):
    graph_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media"
    create_post_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media_publish"

    payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': FACEBOOK_PAGE_TOKEN
    }
    media_res = requests.post(graph_url, data=payload).json()
    creation_id = media_res.get("id")
    if creation_id:
        publish_payload = {
            'creation_id': creation_id,
            'access_token': FACEBOOK_PAGE_TOKEN
        }
        publish_res = requests.post(create_post_url, data=publish_payload)
        if publish_res.status_code == 200:
            print("Posted to Instagram!")
        else:
            print("Instagram post failed:", publish_res.text)
    else:
        print("Instagram media creation failed:", media_res)

# Post to Twitter using tweepy and OAuth1.0a
"""def post_to_twitter(message):
    try:
        auth = tweepy.OAuth1UserHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        api = tweepy.API(auth)
        status = api.update_status(status=message)
        print("Tweet posted successfully!")
    except tweepy.TweepyException as e:
        # safer error info printing
        status_code = getattr(e.response, 'status_code', 'No status code')
        api_codes = getattr(e, 'api_codes', 'No API codes')
        error_msg = str(e)
        print(f"❌ Tweeting failed: HTTP {status_code} - API codes {api_codes} - Message: {error_msg}")

COMPANY_URN = os.getenv("COMPANY_URN")

headers = {
    "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
    "X-Restli-Protocol-Version": "2.0.0",
    "Content-Type": "application/json"
}

# Step 1: Register the image for upload
def register_upload():
    upload_request = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": COMPANY_URN,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    response = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers=headers,
        json=upload_request
    )
    response.raise_for_status()
    data = response.json()
    return data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"], \
           data["value"]["asset"]

# Step 2: Upload the image
def upload_image(image_url, upload_url):
    image_data = requests.get(image_url).content
    upload_headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/octet-stream"
    }
    upload_response = requests.put(upload_url, headers=upload_headers, data=image_data)
    upload_response.raise_for_status()

# Step 3: Create the company post
def create_post(image_asset_urn, text):
    post_data = {
        "author": COMPANY_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{
                    "status": "READY",
                    "description": {"text": "Company post image"},
                    "media": image_asset_urn,
                    "title": {"text": "Post Image"}
                }]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    post_response = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=post_data)
    post_response.raise_for_status()
    return post_response.json()"""
# Main script
if __name__ == "__main__":
    retriever = build_retriever("https://cloudjune.com")

    topic = input("What do you want to post about today? ")
    caption = generate_caption(topic, retriever)
    print("\nGenerated caption:\n", caption)
    image_url = generate_image(caption)
    confirm = input("Do you want to proceed with posting? (y/n): ").lower()
    if confirm != 'y':
        print("Aborted.")
        exit()

    platforms = input("Which platforms to post to? (facebook, instagram, twitter, linkedin, all): ").lower()

    if platforms in ["facebook", "all"]:
        post_to_facebook(caption, image_url)

    if platforms in ["instagram", "all"]:
        if image_url:
            post_to_instagram(caption, image_url)
        else:
            print("Instagram post requires an image. Skipping.")

    """if platforms in ["twitter", "all"]:
        post_to_twitter(caption)

    if platforms in ["linkedin", "all"]:
        post_to_linkedin(caption, image_url)"""
    
    #git branch -M main