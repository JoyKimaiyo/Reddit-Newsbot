#!/usr/bin/env python3
"""
Automated Reddit Scraper: Scrapes 20 'hot' posts from predefined subreddits
"""

import praw
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Reddit API credentials
REDDIT_CLIENT_ID = "FF6_aD4l1Ghdp7vLpxWl5Q"
REDDIT_SECRET = "4max2TMGDGKurYRAX2-iWLAYCDIhfA"
REDDIT_APP_NAME = "newsbot"
REDDIT_USERNAME = "ExistingManner4433"
REDDIT_PASSWORD = "Timmy@2013"

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("DB_PASSWORD") or input("Enter MySQL root password: "),
    "database": "reddit_posts",
    "auth_plugin": "mysql_native_password"
}

# Subreddits to scrape
SUBREDDITS = [
    'datascience',
    'MachineLearning',
    'LanguageTechnology',
    'deeplearning',
    'datasets',
    'visualization',
    'dataisbeautiful',
    'learnpython'
]

def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def create_table():
    conn = connect_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reddit_posts (
                post_id VARCHAR(20) PRIMARY KEY,
                title TEXT,
                selftext TEXT,
                url TEXT,
                author VARCHAR(50),
                score INT,
                publish_date DATETIME,
                num_of_comments INT,
                permalink TEXT,
                flair TEXT,
                subreddit VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                full_text TEXT
            )
        """)
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_reddit_client():
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_APP_NAME,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD
        )
        reddit.user.me()  # test credentials
        return reddit
    except Exception as e:
        print(f"Reddit authentication failed: {e}")
        sys.exit(1)

def insert_post(post):
    conn = connect_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reddit_posts (
                post_id, title, selftext, url, author, score,
                publish_date, num_of_comments, permalink,
                flair, subreddit, full_text
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title=VALUES(title),
                selftext=VALUES(selftext),
                score=VALUES(score),
                num_of_comments=VALUES(num_of_comments),
                full_text=VALUES(full_text)
        """, (
            post['post_id'],
            post['title'],
            post['selftext'],
            post['url'],
            post['author'],
            post['score'],
            post['publish_date'],
            post['num_of_comments'],
            post['permalink'],
            post['flair'],
            post['subreddit'],
            post['full_text']
        ))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Insert error: {err}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def scrape_posts(subreddit_name, limit=20):
    reddit = get_reddit_client()
    print(f"\nScraping r/{subreddit_name} (hot, {limit} posts)...")

    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = subreddit.hot(limit=limit)

        saved = 0
        for post in posts:
            if post.stickied:
                continue

            post_data = {
                'post_id': post.id,
                'title': post.title,
                'selftext': post.selftext if post.selftext not in ["[removed]", "[deleted]"] else "",
                'url': post.url,
                'author': str(post.author),
                'score': post.score,
                'publish_date': datetime.utcfromtimestamp(post.created_utc),
                'num_of_comments': post.num_comments,
                'permalink': post.permalink,
                'flair': post.link_flair_text or "",
                'subreddit': subreddit_name,
                'full_text': f"{post.title}\n\n{post.selftext}" if post.selftext else post.title
            }

            if insert_post(post_data):
                saved += 1

        print(f"✅ Saved {saved}/{limit} posts from r/{subreddit_name}")
    except Exception as e:
        print(f"Error scraping r/{subreddit_name}: {e}")

def main():
    print("🚀 Reddit Scraper (automated batch mode)")
    print("=" * 40)
    
    if not create_table():
        print("❌ Table creation failed. Exiting.")
        return

    for sub in SUBREDDITS:
        scrape_posts(subreddit_name=sub, limit=20)

if __name__ == "__main__":
    main()


