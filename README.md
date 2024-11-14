# InboxZing! 🗞️
Projects in Programming and Data Sciences - Final Project

## Group Members 👥

Rohan Sabu

Komal Neupane

Ali Tamer

Olivia Xiang

## Overview 📰
InboxZing! (this is an initial prototype) is a web application that allows users to receive news articles tailored to their preferences based on country, category, and language. Users can create accounts, manage their preferences, and view articles with summaries in a preferred style.

## Features 👉
User Management: Create accounts with unique usernames and emails.

News Customization: Select preferred countries, languages, and categories to receive personalized news feeds.

News API Integration: Fetches real-time headlines from various countries and categories.

Database Storage: Stores users, preferences, and articles in MongoDB.

## Usage 📝
User Registration: Users can register with a unique username and email.

Preferences Setup: Users specify their preferred countries, languages, and categories.

Fetch News: The app fetches news based on user preferences and displays the latest headlines.

## Tech Stack 💾
Python: Core language

MongoDB: Database for storing user data and articles

News API: Third-party API for fetching news headlines

## Data Model 👨‍💻

### Collections in MongoDB
The app utilizes MongoDB to store the following collections:

1. **Users Collection (`users`)**
   - **username** (String): Unique identifier for the user.
   - **password** (String): Hashed password for authentication.
   - **email** (String): User's email address.
   - **created_at** (Date): Timestamp of account creation.
   - **preferences** (Object): User preferences including:
     - **country** (String): Selected country for news articles.
     - **category** (String): Selected news category.
     - **language** (String): Preferred language for articles.
     - **summaryStyle** (String): Preferred summary style (brief/detailed).

2. **Preferences Collection (`preferences`)**
   - Although preferences are currently stored within the users collection, you could separate this into its own collection if needed for complex preference management.

3. **News Articles Collection (`news_articles`)**
   - **username** (String): Username of the user who fetched the article.
   - **fetched_at** (Date): Timestamp when the articles were fetched.
   - **preferences** (Object): The preferences used to fetch the articles.
   - **article** (Object): Article details including:
     - **title** (String): Title of the news article.
     - **source** (String): Source of the news article.
     - **description** (String): Brief description of the article.
     - **url** (String): Link to the full article.
     - **published_at** (Date): Date when the article was published.

## Why MongoDB? 🤔

We chose **MongoDB** for this project due to the following reasons:
- **Schema Flexibility**: MongoDB allows for dynamic schemas, which is ideal for a news application where user preferences and articles can vary significantly.
- **Scalability**: It can handle large volumes of data efficiently, making it suitable for storing numerous articles fetched from various sources.
- **Performance**: MongoDB's document-oriented structure enables fast data retrieval, which is great for for providing users with timely news updates.

## Setup Instructions 💻

### Prerequisites
- Python 3.x
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account for database setup
- [NewsAPI](https://newsapi.org) account to obtain an API key

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/rohanv32/InboxZing.git
   cd InboxZing

2. **Create a Virtual Environment**

   Creating a virtual environment helps keep your project dependencies isolated.

      ```bash
      python -m venv venv
      source venv/bin/activate  
      # On Windows use `venv\Scripts\activate`

3. **Install Dependencies**


   To install the required dependencies for the project, run:

      ```bash
      pip install -r requirements.txt

4. **Set Up MongoDB**

     Create a new cluster in MongoDB Atlas.
   
     Add a database user with read and write permissions.
   
     Whitelist your IP address for database access.
   
     Obtain your connection string from MongoDB Atlas and replace the placeholder in the code with your connection string.
   

5. **Configure Environment Variables**

   Create a .env File, make sure to replace username, password, and your_news_api_key_here with your actual MongoDB and NewsAPI credentials:
   
      ```bash
      MONGO_URI=mongodb+srv://<username>:<password>@newcluster.hj9pw.mongodb.net/?retryWrites=true&w=majority&appName=NewCluster
      NEWS_API_KEY=your_news_api_key_here

6. **Run the Application**

     Once you have set up your virtual environment, installed dependencies, and configured MongoDB and NewsAPI, you can run the application's backend:

      ```bash
        python3 api.py

6. **Frontend Guide**

     Please go to https://github.com/rohanv32/InboxZingReact and follow the set up instructions there.

## License 📎
This project is licensed under the MIT license.
