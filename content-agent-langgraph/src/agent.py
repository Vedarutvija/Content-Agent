# filepath: content-agent-langgraph/content-agent-langgraph/src/agent.py
import os
import openai
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from utils.social_media import post_to_facebook, post_to_instagram, post_to_twitter, post_to_linkedin, schedule_to_platforms, convert_gst_to_utc
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime, timedelta
import pytz
# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the LangGraph agent
class LangGraphAgent:
    def __init__(self, url: str):
        self.retrieved_docs = [
    type("Doc", (object,), {"page_content": page["content"], "metadata": {"source": page["url"]}})
    for page in LangGraphAgent.crawl_website(url)]

    # Helper: Retrieve web content and build retriever 

    def is_valid_url(url, domain):
        return urlparse(url).netloc == urlparse(domain).netloc

    def crawl_website(start_url, max_pages=20):
        visited = set()
        to_visit = [start_url]
        pages = []

        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue
            try:
                response = requests.get(url, timeout=10)
                visited.add(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text(separator=' ', strip=True)
                    pages.append({"url": url, "content": text})

                    for link in soup.find_all('a', href=True):
                        full_url = urljoin(url, link['href'])
                        if LangGraphAgent.is_valid_url(full_url, start_url) and full_url not in visited:
                            to_visit.append(full_url)

                    time.sleep(1)  # be respectful of rate limits
            except Exception as e:
                print(f"Error fetching {url}: {e}")

        return pages


# Generate caption using LangChain RAG pipeline
    def generate_caption_and_content(self, topic, retrieved_docs):
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # Combine retrieved content
        context = "\n\n".join([f"{i+1}. {doc.page_content}" for i, doc in enumerate(retrieved_docs[:5])])

        # Prompt for generation
        prompt = f"""
    You are a B2B tech content strategist. Based on the topic and contextual content below, write:

    1. A professional LinkedIn **caption** (max 250 characters) designed to spark interest.
    2. A concise and informative **LinkedIn post body** (80–150 words) written in simple, authoritative tone.

    Topic: {topic}

    Context from website content:
    {context}

    Format:
    CAPTION: <caption here>
    CONTENT: <content here>
    """

        response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
        )
        output = response.choices[0].message.content

        # Extract caption and content robustly
        caption = ""
        content = ""
        if "CAPTION:" in output and "CONTENT:" in output:
            caption = output.split("CAPTION:")[1].split("CONTENT:")[0].strip()
            content = output.split("CONTENT:")[1].strip()
        else:
            caption = "⚠️ Could not parse caption"
            content = output.strip()

        return caption, content

    def generate_image(self, prompt: str) -> str:
        try:
            response = openai.images.generate(
                model="dall-e-3", 
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

    def post_to_platforms(self, caption: str, content: str, image_url: str, platforms: list):
        post_body = f"{caption}\n\n{content}"
        if "facebook" in platforms:
            post_to_facebook(post_body, image_url)
        if "instagram" in platforms:
            if image_url:
                post_to_instagram(post_body, image_url)
        if "twitter" in platforms:
            post_to_twitter(post_body)
        if "linkedin" in platforms:
            post_to_linkedin(post_body, image_url)


# Main script
if __name__ == "__main__":
    agent = LangGraphAgent("https://cloudjune.com")
    topic = input("What do you want to post about today? ")
    caption, content = agent.generate_caption_and_content(topic, agent.retrieved_docs)
    print("\nGenerated caption:\n", caption)
    print("\nGenerated content:\n", content)
    image_url = agent.generate_image(topic)
    if not image_url:
        print("Image generation failed, proceeding without image.")
    platforms = input("Which platforms to post to? (facebook, instagram, twitter, linkedin, all): ").lower().split(", ")
    if "all" in platforms:
        platforms = ["facebook", "instagram", "twitter", "linkedin"]
    scheduling = input("Do you want to schedule the post? (y/n): ").lower()

if scheduling == 'y':
    user_input = input("Enter post time in GST (YYYY-MM-DD HH:MM): ")
    try:
        scheduled_time_utc = convert_gst_to_utc(user_input)
        now_utc = datetime.now(pytz.utc)
        if scheduled_time_utc <= now_utc + timedelta(minutes=20):
            raise ValueError("Time must be at least 20 minutes in the future (in UTC).")
        schedule_to_platforms(caption, image_url, platforms, scheduled_time_utc)
    except ValueError as e:
        print("❌ Error:", e)
elif scheduling == 'n':
    agent.post_to_platforms(caption, content, image_url, platforms)
    print("✅ Post published immediately!")
else:
    print("❌ Invalid input. Please enter 'y' or 'n'.")