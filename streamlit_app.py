import streamlit as st
import sqlite3
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import os

# SQLite DB connection
def create_connection():
    conn = sqlite3.connect('perfume_app.db')
    return conn

# Function to create database tables
def create_database():
    conn = create_connection()
    cursor = conn.cursor()
    
    # Create the 'users' table for storing login credentials
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL)''')
    
    # Create the 'history' table to store user preferences and recommendations
    cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        preferences TEXT,
                        recommendations TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# Function to register a new user
def register_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

# Function to authenticate a user
def authenticate_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Function to store user preferences and recommendations
def store_preferences(user_id, preferences, recommendations):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        cursor.execute("INSERT INTO history (user_id, preferences, recommendations) VALUES (?, ?, ?)", 
                       (user_id, preferences, recommendations))
        conn.commit()
    conn.close()

# Function to load the perfume data from CSV
def load_perfume_data():
    df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
    df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")
    return df

# Function to perform AI-based perfume recommendation using Sentence Transformers
def recommend_perfume(preferences, df):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query = " ".join(preferences.values())
    
    query_embedding = model.encode(query, convert_to_tensor=True)
    perfume_embeddings = model.encode(df["combined"].tolist(), convert_to_tensor=True)
    
    cosine_scores = util.pytorch_cos_sim(query_embedding, perfume_embeddings)[0]
    top_results = cosine_scores.topk(5)
    
    recommendations = []
    for score, idx in zip(top_results[0], top_results[1]):
        recommendations.append((df.iloc[idx]["Name"], df.iloc[idx]["Brand"], score.item()))
    
    return recommendations

# Show the AI-based perfume recommendations
def show_recommendations():
    preferences = st.session_state.answers
    mood = preferences.get("mood")
    occasion = preferences.get("occasion")
    notes = preferences.get("notes")

    df = load_perfume_data()
    recommendations = recommend_perfume(preferences, df)

    if recommendations:
        for name, brand, score in recommendations:
            st.markdown(f"### *{name}* by {brand} - Score: {score:.2f}")
    else:
        st.error("No recommendations found!")

    # Store preferences and recommendations in the database
    user_id = st.session_state.user_id
    store_preferences(user_id, str(preferences), ", ".join([name for name, _, _ in recommendations]))

    st.experimental_rerun()

# Function for login page
def show_login():
    st.title("Login Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.step = 1
            st.session_state.answers = {}
            st.success("Login successful! Redirecting to quiz...")
            st.experimental_rerun()  # Now works after login
        else:
            st.error("Invalid credentials, please try again.")

# Function for registration page
def show_registration():
    st.title("Register Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if password != confirm_password:
            st.error("Passwords do not match!")
        else:
            register_user(username, password)
            st.success("Registration successful! Please log in.")

# Function to show the questionnaire page
def show_questionnaire():
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'answers' not in st.session_state:
        st.session_state.answers = {}

    if st.session_state.step == 1:
        st.subheader("Step 1: What's your current vibe?")
        mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
        if st.button("Next ➡"):
            st.session_state.answers["mood"] = mood
            st.session_state.step = 2
            st.experimental_rerun()

    elif st.session_state.step == 2:
        st.subheader("Step 2: What's the occasion?")
        occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])
        if st.button("Next ➡"):
            st.session_state.answers["occasion"] = occasion
            st.session_state.step = 3
            st.experimental_rerun()

    elif st.session_state.step == 3:
        st.subheader("Step 3: What kind of notes do you love?")
        notes = st.multiselect("Pick a few that speak to your soul 💫", 
                               ["Vanilla", "Oud", "Citrus", "Floral", "Spicy", "Woody", "Sweet", "Musky"])
        if st.button("Get My Recommendations 💖"):
            st.session_state.answers["notes"] = notes
            show_recommendations()

# Main app routing logic
def main():
    # Create database tables on app startup (just once)
    create_database()

    page = st.sidebar.radio("Choose a page", ["Login", "Register", "Questionnaire"])

    if page == "Login":
        show_login()
    elif page == "Register":
        show_registration()
    elif page == "Questionnaire":
        if 'user_id' not in st.session_state:
            st.warning("Please log in first.")
        else:
            show_questionnaire()

if __name__ == "__main__":
    main()
