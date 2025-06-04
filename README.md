# content-agent-langgraph

This project implements a LangGraph agent designed to generate engaging social media content and automate posting across various platforms. 

## Project Structure

```
content-agent-langgraph
├── src
│   ├── agent.py          # Main logic for the LangGraph agent
│   ├── utils
│   │   └── social_media.py # Utility functions for social media API interactions
│   └── types
│       └── index.py      # Custom types and interfaces for type safety
├── .env                  # Environment variables for API keys and tokens
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd content-agent-langgraph
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add your API keys and tokens:
   ```
   OPENAI_API_KEY=your_openai_api_key
   FACEBOOK_PAGE_ID=your_facebook_page_id
   FACEBOOK_PAGE_TOKEN=your_facebook_page_token
   INSTAGRAM_USER_ID=your_instagram_user_id
   TWITTER_CONSUMER_KEY=your_twitter_consumer_key
   TWITTER_CONSUMER_SECRET=your_twitter_consumer_secret
   TWITTER_ACCESS_TOKEN=your_twitter_access_token
   TWITTER_ACCESS_SECRET=your_twitter_access_secret
   PIXABAY_API_KEY=your_pixabay_api_key
   LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
   LINKEDIN_ORGANIZATION_ID=your_linkedin_organization_id
   ```

## Usage

1. **Run the agent:**
   Execute the main script to start generating captions and posting to social media:
   ```bash
   python src/agent.py
   ```

2. **Follow the prompts:**
   The agent will ask for the topic you want to post about and the platforms you wish to use.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Tokens

Required tokens: OpenAI API key, Facebook Page Access Token, Facebook Page ID, Instagram Account ID

1. **Facebook Page Access Token and Facebook Page ID:**
   - Create a facebook account
   - Create a page
   - Create a business portfolio on meta business suite (Sign in using your facebook account)
   - Connect your facebook account and the page
   - Grant the business portfolio full access to the page
   - Go to meta for developers (Sign in using your facebook account)
   - Create an app with use cases 'Manage Everything on Page' and 'Manage messaging and content on Instagram'
   - Connect this app to the business portfolio
   - Under permissions in 'Manage Everything on Page' allow the following: 'business_management', 'pages_manage_engagement', 'pages_manage_posts', 'pages_manage_metadata', 'pages_read_engagement', pages_read_user_content', 'pages_show_list', 'public_profile'
   - Go to the graph API
   - Allow all the permissions mentioned  above
   - Click generate access token
   - this is NOT your page access token, enter GET graph.facebook.com/v22.0/me/accounts
   - You should get a 'data' list -> If you see an empty list, make sure your page is connected to the business portfolio and that your facebook account is the admin of that page
   - In this list, the 'access_token' field consists of your page access token, this token will remain valid for 1 hour
   - The 'id' field under the 'name' field consists of your page ID
2. **Instagram Account ID:**
   - Create an instagram business account using your facebook account
   - Connect this instagram account to your business portfolio
   - Connect this instagram account to your facebook page under 'Linked Accounts'
   - Go back to your app, under 'Manage messaging and content on Instagram', add the following permissions: 'business_management', 'instagram_basic', 'instagram_content_publish', 'instagram_manage_comments', 'instagram_manage_insights', 'instagram_manage_messages', 'instagram_manage_upcoming_events', 'pages_read_engagement', 'pages_show_list', 'public_profile'
   - Go to the graph API, allow the above permissions
   - Enter GET graph.facebook.com/v22.0/me/accounts, the access token given in the 'access_token' field is your new page access token, page ID remains the same
   - Go back to your meta business suite, click on your instagram account, the ID shown above the name of your instagram account is your instagram account ID
