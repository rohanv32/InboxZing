import requests
from pymongo import MongoClient
from datetime import datetime, timedelta
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

client = MongoClient(MONGO_URI)
db = client['news_app']
users_collection = db['users']
# Ensuring that username and password are unique
users_collection.create_index([("username", 1)], unique=True)
users_collection.create_index([("email", 1)], unique=True)
preferences_collection = db['preferences']
news_articles_collection = db['news_articles']

NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# available countries, languages and categories as given by the api

country_codes = ['ae', 'ar', 'at', 'au', 'be', 'bg', 'br', 'ca', 'ch', 'cn', 'co', 'cu', 'cz', 'de', 'eg', 'fr',
                       'gb', 'gr', 'hk', 'hu', 'id', 'ie', 'il', 'in', 'it', 'jp', 'kr', 'lt', 'lv', 'ma', 'mx', 'my',
                       'ng', 'nl', 'no', 'nz', 'ph', 'pl', 'pt', 'ro', 'rs', 'ru', 'sa', 'se', 'sg', 'si', 'sk', 'th',
                       'tr', 'tw', 'ua', 'us', 've', 'za']

# Created a dictionary to map all countries and codes to be easier for user
country_names = {
    'ae': 'United Arab Emirates', 'ar': 'Argentina', 'at': 'Austria', 'au': 'Australia', 'be': 'Belgium', 'bg': 'Bulgaria',
    'br': 'Brazil', 'ca': 'Canada', 'ch': 'Switzerland', 'cn': 'China', 'co': 'Colombia', 'cu': 'Cuba', 'cz': 'Czech Republic',
    'de': 'Germany', 'eg': 'Egypt', 'fr': 'France', 'gb': 'United Kingdom', 'gr': 'Greece', 'hk': 'Hong Kong', 'hu': 'Hungary',
    'id': 'Indonesia', 'ie': 'Ireland', 'il': 'Israel', 'in': 'India', 'it': 'Italy', 'jp': 'Japan', 'kr': 'South Korea',
    'lt': 'Lithuania', 'lv': 'Latvia', 'ma': 'Morocco', 'mx': 'Mexico', 'my': 'Malaysia', 'ng': 'Nigeria', 'nl': 'Netherlands',
    'no': 'Norway', 'nz': 'New Zealand', 'ph': 'Philippines', 'pl': 'Poland', 'pt': 'Portugal', 'ro': 'Romania', 'rs': 'Serbia',
    'ru': 'Russia', 'sa': 'Saudi Arabia', 'se': 'Sweden', 'sg': 'Singapore', 'si': 'Slovenia', 'sk': 'Slovakia', 'th': 'Thailand',
    'tr': 'Turkey', 'tw': 'Taiwan', 'ua': 'Ukraine', 'us': 'United States', 've': 'Venezuela', 'za': 'South Africa'
}

categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']

language_codes = ['ar', 'de', 'en', 'es', 'fr', 'he', 'it', 'nl', 'no', 'pt', 'ru', 'se', 'ud', 'zh']

# created a dictionary to put all the languages with their codes to be easier for user access
languages = {
    'ar': 'Arabic', 'de': 'German', 'en': 'English', 'es': 'Spanish', 'fr': 'French', 'he': 'Hebrew',
    'it': 'Italian', 'nl': 'Dutch', 'no': 'Norwegian', 'pt': 'Portuguese', 'ru': 'Russian', 'se': 'Swedish',
    'ud': 'Urdu', 'zh': 'Chinese'
}