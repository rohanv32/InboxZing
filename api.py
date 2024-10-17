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

# Model used to Capture user sign up credentials.
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# Model used to capture login credentials for logging in of an existing user
class UserLogin(BaseModel):
    username: str
    password: str

# Model that is used to Stores the user's news preferences
# it captures info of country, category, language, and news frequency.
class UserPreferences(BaseModel):
    country: str
    category: str
    language: str
    summaryStyle: str
    frequency: int

# Model used to capture the news articles that match user preferences
class NewsArticle(BaseModel):
    title: str
    source: str
    description: str
    url: str
    published_at: Optional[str]
    summary: str

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
        
# All endpoints are added below
# first endpoint to handle signing up a a new user
@fast_app.post("/signup")
async def signup(user: UserCreate):
    # hash the user's password for security
    hashed_password = hash_password(user.password)
    new_user = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.now()
    }
    # message displayed when user is created
    # then a user is successfully added to the database
    try:
        users_collection.insert_one(new_user)
        return {"message": "User created successfully"}
        # if error display this message
        # errors include having same usernames and emails like another user(duplication)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")   
    
# Second Endpoint to handle logging in a user
@fast_app.post("/login")
async def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if db_user and db_user["password"] == hash_password(user.password):
      # if username and password match user in db, login is successful
        return {"message": "Login successful"}
        # if error display this message
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Third Endpoint to handle modifying of previously set user preferences
@fast_app.put("/preferences/{username}")
async def update_preferences(username: str, preferences: UserPreferences):
  # Update the user's preferences in the database accordingly
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"preferences": preferences.dict()}}
    )
    # error handling if prefs are updated successfully
    # if error, user not found displayed
    if result.modified_count:
        return {"message": "Preferences updated successfully"}
    raise HTTPException(status_code=404, detail="User not found")

# Fourth endpoint to get news articles based on user preferences pre-set
@fast_app.get("/news/{username}")
async def get_news(username: str):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    preferences = user.get("preferences")
    if not preferences:
        raise HTTPException(status_code=400, detail="User preferences not set")

    last_article = news_articles_collection.find_one({"username": username}, sort=[("fetched_at", -1)])

    # Check if we need to fetch new articles based on frequency
    if last_article and datetime.now() - last_article['fetched_at'] < timedelta(hours=preferences['frequency']):
        articles = list(news_articles_collection.find({"username": username}))
    else:
      # Clear old articles
        news_articles_collection.delete_many({"username": username})
        fetched_articles = fetch_news(UserPreferences(**preferences))

        articles = []
        for article in fetched_articles:
            summary = summarize_article(article, preferences['summaryStyle'])
            news_entry = {
                "username": username,
                "fetched_at": datetime.now(),
                "preferences": preferences,
                "article": {
                    "title": article['title'],
                    "source": article['source']['name'],
                    "description": article['description'],
                    "url": article['url'],
                    "published_at": article.get('publishedAt'),
                    "summary": summary
                }
            }
            news_articles_collection.insert_one(news_entry)
            # Add the _id as a string to the result
            news_entry['_id'] = str(news_entry['_id'])
            articles.append(news_entry)

    # Convert ObjectId to string for all articles
    for article in articles:
        article['_id'] = str(article['_id'])

    return {"articles": articles}


# fifth endpoint to get all news articles stored in the database
@fast_app.get("/news_articles/")
async def get_news_articles():
    articles = list(news_articles_collection.find())
    # for mongoDB : Change the news ObjectIds to string same as endpoint 4
    for article in articles:
        article["_id"] = str(article["_id"])
    return articles

# fifth endpoint to get all news articles stored in the database
@fast_app.get("/news_articles/")
async def get_news_articles():
    articles = list(news_articles_collection.find())
    # for mongoDB : Change the news ObjectIds to string same as endpoint 4
    for article in articles:
        article["_id"] = str(article["_id"])
    return articles

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fast_app, host="0.0.0.0", port=8000)