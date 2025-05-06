#!/usr/bin/env python3
"""
Streamlit Newsbot Viewer for Reddit Posts
"""

import streamlit as st
import mysql.connector
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from PIL import Image

# Load environment variables
load_dotenv()

# MySQL Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("DB_PASSWORD"),
    "database": "reddit_posts",
    "auth_plugin": "mysql_native_password"
}

def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        st.error(f"Database connection failed: {err}")
        return None

def fetch_posts(subreddit=None, limit=20):
    conn = get_connection()
    if not conn:
        return []

    query = "SELECT title, url, score, subreddit, publish_date, full_text FROM reddit_posts"
    params = []

    if subreddit and subreddit != "All":
        query += " WHERE subreddit = %s"
        params.append(subreddit)

    query += " ORDER BY publish_date DESC LIMIT %s"
    params.append(limit)

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        st.error(f"Failed to fetch posts: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def generate_with_gemini(prompt):
    api_key = os.getenv("GEM_API")
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Error: {e}"

# Streamlit UI Config
st.set_page_config(page_title="Reddit Newsbot", layout="wide")

# Top: Small logo on the left and title on the right
image = Image.open("communityIcon_hrq90p2z27k11 (2).jpg")
col_logo, col_title = st.columns([1, 10])
with col_logo:
    st.image(image, width=60)
with col_title:
    st.markdown("<h1>Reddit Newsbot</h1>", unsafe_allow_html=True)

# App description
with st.container():
    st.markdown("""
    > *Keeping up with the new trends in any technological field is important. Tech changes everyday — 
    you don't want to be passed by the new tools and skills in data.*

    Reddit helps users stay updated on the latest news and trends. Its forum-style structure facilitates real-time 
    discussions and insights on ongoing events. Reddit fosters a sense of community among its users and has emerged as 
    an indispensable platform for tech enthusiasts looking to stay abreast of the ever-changing technology landscape.

    **This app** offers an opportunity to:
    - Keep updated with the latest news in the data field
    - Explore hot topics from leading subreddits
    - Get AI assistance to understand key concepts and tools
    """)

# Sidebar
with st.sidebar:
    st.header("🔍 Explore Topics")
    subreddits = [
        'All',
        'datascience',
        'MachineLearning',
        'LanguageTechnology',
        'deeplearning',
        'datasets',
        'visualization',
        'dataisbeautiful',
        'learnpython'
    ]
    sub_filter = st.selectbox("Choose a Subreddit", subreddits)
    limit = st.slider("Number of Posts", 5, 100, 20)

    st.markdown("---")
    st.subheader("ℹ️ About")
    st.info("This tool fetches the latest hot Reddit posts from top tech and data subreddits.")

    st.subheader("📘 How to Use")
    st.markdown("""
    - Select a subreddit to explore
    - Set the number of posts to view
    - Click each heading to expand and read
    - Use the provided link to view original thread
    """)

# Main area
if sub_filter != "All":
    all_posts = fetch_posts(sub_filter, limit)
    if not all_posts:
        st.warning("No posts found.")
    else:
        st.markdown("---")

        # Side-by-side layout for posts and AI explanation
        left_col, right_col = st.columns([3, 1], gap="large")

        with left_col:
            st.markdown(f"### 🔥 Hot posts from r/{sub_filter}")

            num_to_show = 5
            if "visible_posts" not in st.session_state:
                st.session_state.visible_posts = num_to_show

            for i, post in enumerate(all_posts[:st.session_state.visible_posts]):
                with st.expander(f"{post['title']} ({post['score']} upvotes)"):
                    st.markdown(f"**Subreddit:** r/{post['subreddit']}")
                    st.markdown(f"**Published:** {post['publish_date'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(post["full_text"][:1500] + ("..." if len(post["full_text"]) > 1500 else ""))
                    st.markdown(f"[View on Reddit](https://reddit.com{post['url']})")

            if st.session_state.visible_posts < len(all_posts):
                if st.button("Show More"):
                    st.session_state.visible_posts += 5

        with right_col:
            st.subheader("🧠 Need Help Understanding a Keyword?")
            keyword = st.text_input("Enter a keyword you'd like explained:")
            if keyword:
                with st.spinner("Thinking..."):
                    explanation = generate_with_gemini(f"Explain the concept of '{keyword}' in simple terms for a data enthusiast.")
                    st.markdown(f"**Explanation for '{keyword}':**")
                    st.markdown(explanation)
else:
    st.info("👈 Select a subreddit from the sidebar to begin exploring hot topics.")

# Footer
st.markdown("---")
st.markdown("<center>© 2025 Created by Joyce Kimaiyo</center>", unsafe_allow_html=True)
