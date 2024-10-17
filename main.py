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

# Fetch news articles based on user preferences
# Using the news API and the preferences chosen by the user with a limit of news articles
def fetch_news(preferences):
    params = {
        'apiKey': NEWS_API_KEY,
        'country': preferences['country'],
        'category': preferences['category'],
        'language': preferences['language'],
        'pageSize': 10
    }

    response = requests.get(NEWS_API_URL, params=params)

    if response.status_code == 200:
        return response.json().get('articles', [])
    else:
        return []
    
#Utility function to check how much time has passes since the user last logged in and fetched news articles
def has_time_passed(last_fetched_time, frequency_in_hours):
    time_difference = datetime.now() - last_fetched_time
    return time_difference > timedelta(hours=frequency_in_hours)

#Utility function to summarise articles based on the user's preferred style
def summarize_article(article, summary_style):
    if summary_style == 'brief':
        return f"Title: {article['title']}\nSource: {article['source']['name']}\n"
    elif summary_style == 'humorous':
        return f"Title: {article['title']} - Brought to you by the always trustworthy {article['source']['name']}!\n"
    elif summary_style == 'eli5':
        return f"This article titled '{article['title']}' from {article['source']['name']} is basically saying: {article['description']}.\n"
    else:
        return f"Title: {article['title']}\nSource: {article['source']['name']}\nDescription: {article['description']}\nURL: {article['url']}\n"
    
def display_news(username):
    preferences = get_user_preferences(username)
    if not preferences:
        print("No preferences found. Please set them up.")
        return

    # Retrieving the the last fetched article for the user
    last_article = news_articles_collection.find_one({"username": username}, sort=[("fetched_at", -1)])

    # Checking if enough time has passed based on the user’s frequency setting
    if last_article and not has_time_passed(last_article['fetched_at'], preferences['frequency']):
        # If the time hasn't passed, fetch the existing articles
        print("Fetching previously stored articles...\n")
        articles = list(news_articles_collection.find({"username": username}))

        for article in articles:

            title = article['article']['title']
            summary = article['article']['summary']
            url = article['article']['url']


            print(f"Title: {title}")
            print(f"Summary: {summary}")
            print(f"URL: {url}\n")

    else:
        # Time has passed, so delete the old articles and fetch the new ones
        print("Fetching new articles...\n")
        delete_articles(username)

        articles = fetch_news(preferences)

        if not articles:
            print("No articles found.")
            return

        print("\nLatest News Articles:\n")
        for article in articles:
            # Creating the summary based on user’s summary style
            article_summary = summarize_article(article, preferences['summaryStyle'])

            print(article_summary)

            # Creating an entry for the article in the database with the username and preferences
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

# Function used to delete the articles if the preferred frequency time has passed
def delete_articles(username):
    result = news_articles_collection.delete_many({"username": username})
    print(f"Deleted {result.deleted_count} old articles for user: {username}")

def main():
    while True:
        print("Welcome to the Personalized News App")
        action = input("Do you want to login or signup? (login/signup): ").strip().lower()

        if action == "signup":
            while True:
                email = input("Enter your email: ").strip()
                if users_collection.find_one({"email": email}):
                    print("Error creating user: This email address is already associated with another user. Please enter another email address.")
                    continue

                break

            while True:
                username = input("Enter a username: ").strip()
                if users_collection.find_one({"username": username}):
                    print("Error creating user: This username is already associated with another user. Please enter another username.")
                    continue
                break

            password = input("Enter a password: ").strip()
            create_new_user(username, email, password)
            user_pref_list(username)
            print(f"Account created for {username}. You can now log in.")

        elif action == "login":
            username_input = input("Enter your username: ").strip()
            password = input("Enter your password: ").strip()

            user = users_collection.find_one({"username": username_input})

            if user and user["password"] == hash_password(password):
                print(f"Welcome back, {username_input}!")

                while True:
                    print("\nMenu:")
                    print("1. View your news")
                    print("2. Edit your preferences")
                    print("3. Logout")

                    user_action = input("Select an option (1/2/3): ").strip()

                    if user_action == "1":
                        print("Fetching your news...")
                        display_news(username_input)
                    elif user_action == "2":
                        user_pref_list(username_input)
                    elif user_action == "3":
                        print(f"Logging out {username_input}.")
                        break
                    else:
                        print("Invalid option. Please choose again.")

            else:
                print("Invalid username or password.")
        else:
            print("Invalid option. Please choose either login or signup.")

        exit_app = input("Do you want to exit the app? (yes/no): ").strip().lower()
        if exit_app == "yes":
            break

if __name__ == "__main__":
    main()
