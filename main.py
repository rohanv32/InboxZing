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

def create_new_user(username, email, password):
    hashed_password = hash_password(password)

    user = {"username": username, "password": hashed_password, "email": email, "created_at": datetime.now()}

    try:
        users_collection.insert_one(user)
        print("User created successfully.")
    except Exception as e:
        print(f"Error creating user: {str(e)}")

# function used to find an existing user from the database
def current_user(username):
    try:
        return users_collection.find_one({"username": username})
    except Exception as e:
        print(f"Error finding user: {str(e)}")
        return None
    
# function to hash the password for encryption
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# function for the selection of the user news preference list
def user_pref_list(username):
    # Select the preferred country preference
    print("\nSelect a country from the following list:")
    for code, name in country_names.items():
        print(f"{code}: {name}")
    # if country is invalid display error message
    while True:
        country = input("Enter a country code (e.g., 'us' for United States): ").lower()
        if country not in country_names:
            print("Invalid country code. Please try again.")
        else:
            break

    # Select the category of news wanted from the list
    print("\nSelect a news category from the following list:")
    print(', '.join(categories))
    while True:
        category = input("Enter a category (e.g., 'business'): ").lower()
        # if not in list display error
        if category not in categories:
            print("Invalid category. Please try again.")
        else:
            break

    # Select a language from the list
    print("\nSelect a language from the following list:")
    for code, name in languages.items():
        print(f"{code}: {name}")
    while True:
        language = input("Enter a language code (e.g., 'en' for English): ").lower()
        # if not in list display error
        if language not in languages:
            print("Invalid language code. Please try again.")
        else:
            break

    # Select the summary style wanted for the articles
    summ_styles = ['brief', 'detailed', 'humorous', 'eli5']
    print("\nDo you prefer brief, detailed, humorous, or ELI5 summaries?")
    while True:
        summ_style = input("Enter summary style (brief/detailed/humorous/ELI5): ").strip().lower()
        # if not in list display error
        if summ_style not in summ_styles:
            print("Invalid input. Please choose from brief, detailed, humorous, or ELI5.")
        else:
            break

    # the frequency of the articles is determined by the user by hours
    print("\nHow often would you like to fetch new articles? (in hours, e.g., 1, 3, 24)")
    while True:
        try:
            frequency = int(input("Enter frequency of updates: ").strip())

            if frequency > 0 and frequency < 25:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # user preferences list updated and stored in database of
    preferences = {
        "country": country,
        "category": category,
        "language": language,
        "summaryStyle": summ_style,
        "frequency": frequency
    }

    # Updates the user preferences in the database
    result = users_collection.update_one({"username": username}, {"$set": {"preferences": preferences}})

    if result.modified_count:
        print("Preferences updated successfully.")

        # Delete old articles if preferences are updated
        delete_articles(username)

        # Fetch and store new articles based on updated preferences
        articles = fetch_news(preferences)

        if not articles:
            print("No articles found currently for the preferences you've chosen. Please come back and check again later.")
        else:
            print("New articles fetched and saved:\n")
            for article in articles:
                article_summary = summarize_article(article, preferences['summaryStyle'])

                # Create news entry in the database
                news_entry = {
                    "username": username,
                    "fetched_at": datetime.now(),
                    "preferences": preferences,
                    "article": {
                        "title": article['title'],
                        "source": article['source']['name'],
                        "description": article['description'],
                        "url": article['url'],
                        "published_at": article.get('publishedAt', None),
                        "summary": article_summary
                    }
                }

                # Insert the news entry into the news_articles collection
                news_articles_collection.insert_one(news_entry)
    else:
        print("No changes made or user not found.")

# Function to retrieve user preferences
def get_user_preferences(username):
    user = current_user(username)
    return user.get("preferences") if user else None

