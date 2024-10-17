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