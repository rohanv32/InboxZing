import hashlib
import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId

# loading the env variables and starting the fastapi
load_dotenv()
fast_app = FastAPI()

# connect to database (mongoDB)
MONGO_URI = os.getenv("MONGO_URI")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
client = MongoClient(MONGO_URI)
db = client['news_app']
users_collection = db['users']
news_articles_collection = db['news_articles']

# uniqueness of email and username maintained
users_collection.create_index([("email", 1)], unique=True)
users_collection.create_index([("username", 1)], unique=True)

NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# Password hashing function
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Fetch news articles from NewsAPI based on user preferences
def fetch_news(preferences: UserPreferences) -> List[dict]:
    params = {
        'apiKey': NEWS_API_KEY,
        'country': preferences.country,
        'category': preferences.category,
        'language': preferences.language,
        'pageSize': 10  # Fetch 10 articles
    }
    response = requests.get(NEWS_API_URL, params=params)
    if response.status_code == 200:
        return response.json().get('articles', [])
    return []

# Summarize news articles based on user-selected style
def summarize_article(article: dict, summary_style: str) -> str:
    if summary_style == 'brief':
        return f"Title: {article['title']}\nSource: {article['source']['name']}\n"
    elif summary_style == 'humorous':
        return f"Title: {article['title']} - Brought to you by the always trustworthy {article['source']['name']}!\n"
    elif summary_style == 'eli5':
        return f"This article titled '{article['title']}' from {article['source']['name']} is basically saying: {article['description']}.\n"
    else:
        return f"Title: {article['title']}\nSource: {article['source']['name']}\nDescription: {article['description']}\nURL: {article['url']}\n"
    

# fifth endpoint to get all news articles stored in the database
@fast_app.get("/news_articles/")
async def get_news_articles():
    articles = list(news_articles_collection.find())
    # for mongoDB : Change the news ObjectIds to string same as endpoint 4
    for article in articles:
        article["_id"] = str(article["_id"])
    return articles

# last endpoint to delete a user from the database with his stored data
@fast_app.delete("/user/{username}")
async def delete_user(username: str):
    # if user is found in db, delete from the database
    result = users_collection.delete_one({"username": username})
    if result.deleted_count:
      # delete the news articles as well
        news_articles_collection.delete_many({"username": username})
        return {"message": f"User {username} and articles associated with the account are deleted"}
    # error handling part when the user is not found
    raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fast_app, host="0.0.0.0", port=8000)