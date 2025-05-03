import asyncio
import nest_asyncio
nest_asyncio.apply()

from duckduckgo_search import DDGS
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool
from datetime import datetime
import os
import streamlit as st

# Set the current date (year-month format)
current_date = datetime.now().strftime("%Y-%m")

# Initialize the model with your API key
model = OpenAIChatCompletionsModel(
    model="llama-3.3-70b-versatile",
    openai_client=AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ.get("GROQ_API_KEY")
    )
)

# Define the search tool for fetching news using DuckDuckGo
@function_tool
def get_news_articles(topic):
    st.info(f"Running DuckDuckGo news search for **{topic}**...")

    # Perform the DuckDuckGo search
    ddg_api = DDGS()
    results = ddg_api.text(f"{topic} {current_date}", max_results=5)

    if results:
        news_results = "\n\n".join(
            [
                f"**Title:** {result['title']}\n**URL:** {result['href']}\n**Description:** {result['body']}"
                for result in results
            ]
        )
        st.write(news_results)
        return news_results
    else:
        return f"Could not find news results for **{topic}**."

# Create a News Agent that fetches the news
news_agent = Agent(
    name="News Assistant",
    instructions="You provide the latest news articles for a given topic using DuckDuckGo search.",
    tools=[get_news_articles],
    model=model
)

# Create an Editor Agent that rewrites the news into publishable articles
editor_agent = Agent(
    name="Editor Assistant",
    instructions="Rewrite and give me a news article ready for publishing. Each news story should be in a separate section.",
    model=model
)

# Define the workflow that runs both agents
def run_news_workflow(topic):
    st.markdown("### Fetching News Articles...")

    # Step 1: Fetch news using the news agent
    news_response = Runner.run_sync(
        news_agent,
        f"Get me the news about {topic} on {current_date}"
    )
    raw_news = news_response.final_output

    # Step 2: Pass the raw news to the editor agent for final formatting
    st.markdown("### Editing the News Articles...")
    edited_news_response = Runner.run_sync(
        editor_agent,
        raw_news
    )
    edited_news = edited_news_response.final_output

    st.success("News article is ready!")
    return edited_news

# Main Streamlit app interface with enhanced UI
def main():
    # Sidebar for instructions and branding
    st.sidebar.title("News Assistant")
    st.sidebar.markdown(
        """
        **Welcome to the News Assistant!**

        1. **Enter a topic** in the input box.
        2. **Click 'Get News'** to fetch and edit the latest news.
        3. Enjoy your ready-to-publish news article!
        """
    )
    st.sidebar.image("https://images.unsplash.com/photo-1557683316-973673baf926?auto=format&fit=crop&w=400&q=80", caption="Stay Informed", use_container_width =True)

    # Main page styling
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 3em;
            font-weight: bold;
            color: #4B8BBE;
            text-align: center;
            margin-bottom: 20px;
        }
        .sub-title {
            font-size: 1.5em;
            text-align: center;
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="main-title">News Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Fetch and transform news for your favorite topics!</div>', unsafe_allow_html=True)

    # Input field and button
    topic = st.text_input("Enter a topic to fetch news:", placeholder="e.g., AI, Climate Change, Space Exploration")

    if st.button("Get News"):
        if topic:
            st.info(f"Searching for news about **{topic}**...")
            try:
                with st.spinner("Fetching and editing news articles..."):
                    news_content = run_news_workflow(topic)
                    st.markdown("### Final News Article:")
                    st.markdown(news_content)
            except Exception as e:
                st.error(f"Error fetching news: {str(e)}")
        else:
            st.warning("Please enter a topic to search.")

if __name__ == "__main__":
    main()
