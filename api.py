import hashlib
import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
import certifi

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

class UserPreferencesResponse(BaseModel):
    username: str
    preferences: dict

class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# loading the env variables and starting the fastapi
load_dotenv()
fast_app = FastAPI()

# connect to database (mongoDB)
MONGO_URI = os.getenv("MONGO_URI")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
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

# Helper function to check the password hash
def verify_password(stored_password: str, provided_password: str) -> bool:
    return stored_password == hash_password(provided_password)

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

@fast_app.get("/status")
async def get_status(username: str = Cookie(None)):
    if username:
        # If a username cookie is present, it means the user is logged in
        return {"isLoggedIn": True, "username": username}
    else:
        # If no cookie, the user is not logged in
        return {"isLoggedIn": False, "username": None}
    
# Endpoint to handle signing up a a new user
@fast_app.post("/signup")
async def signup(user: UserCreate):
    # Hash the user's password for security
    hashed_password = hash_password(user.password)
    
    # Check if the username already exists
    existing_user = users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create the new user document
    new_user = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.now()
    }

    # Try to insert the new user into the database
    try:
        users_collection.insert_one(new_user)
        return {"message": "User created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")
    
# Endpoint to handle logging in a user
@fast_app.post("/login")
async def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if db_user and db_user["password"] == hash_password(user.password):
      # if username and password match user in db, login is successful
        print("Backend login successful for:", user.username)
        return JSONResponse(content={"message": "Login successful", "username": user.username})
        # if error display this message
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Endpoint to handle modifying of previously set user preferences
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

@fast_app.get("/news/{username}")
async def get_news(username: str):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    preferences = user.get("preferences")
    if not preferences:
        raise HTTPException(status_code=400, detail="User preferences not set")

    user_news_doc = news_articles_collection.find_one({"username": username})

    # Check if the preferences have changed (e.g., compare the stored preferences with the current ones)
    if user_news_doc and user_news_doc['preferences'] == preferences:
        if datetime.now() - user_news_doc['fetched_at'] < timedelta(hours=preferences['frequency']):
            # Return the stored articles if they are recent enough
            articles = user_news_doc['articles']
        else:
            # Fetch new articles if the frequency has passed
            fetched_articles = fetch_news(UserPreferences(**preferences))
            articles = []
            for article in fetched_articles:
                summary = summarize_article(article, preferences['summaryStyle'])
                articles.append({
                    "title": article['title'],
                    "source": article['source']['name'],
                    "description": article['description'],
                    "url": article['url'],
                    "published_at": article.get('publishedAt'),
                    "urlToImage": article.get('urlToImage'),
                    "summary": summary
                })

            # Update the user's document with the new articles
            news_articles_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "username": username,
                        "fetched_at": datetime.now(),
                        "preferences": preferences,
                        "articles": articles
                    }
                },
                upsert=True
            )
    else:
        # If preferences have changed, fetch new articles regardless of frequency
        fetched_articles = fetch_news(UserPreferences(**preferences))
        articles = []
        for article in fetched_articles:
            summary = summarize_article(article, preferences['summaryStyle'])
            articles.append({
                "title": article['title'],
                "source": article['source']['name'],
                "description": article['description'],
                "url": article['url'],
                "published_at": article.get('publishedAt'),
                "urlToImage": article.get('urlToImage'),
                "summary": summary
            })

        # Update the user's document with the new articles and preferences
        news_articles_collection.update_one(
            {"username": username},
            {
                "$set": {
                    "username": username,
                    "fetched_at": datetime.now(),
                    "preferences": preferences,
                    "articles": articles
                }
            },
            upsert=True
        )

    return {"articles": articles}


# Endpoint to get preferences for the Profile Page display
@fast_app.get("/user/{username}", response_model=UserPreferencesResponse)
async def get_user_preferences(username: str):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user["username"], "preferences": user.get("preferences", {})}

# Endpoint to handle password update
@fast_app.put("/user/{username}/password")
async def update_user_password(username: str, request: UpdatePasswordRequest):
    # Fetch user from the database
    user = users_collection.find_one({"username": username})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not verify_password(user['password'], request.current_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Hash new password
    hashed_password = hash_password(request.new_password)

    # Update the password in the database
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"password": hashed_password}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Password unchanged")
    
    return {"message": "Password updated successfully"}

# Endpoint to get all news articles stored in the database
@fast_app.get("/news_articles/")
async def get_news_articles():
    articles = list(news_articles_collection.find())
    # for mongoDB : Change the news ObjectIds to string same as endpoint 4
    for article in articles:
        article["_id"] = str(article["_id"])
    return articles

# Endpoint to delete a user from the database with his stored data
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

fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust if your frontend is hosted elsewhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fast_app, host="0.0.0.0", port=8000)