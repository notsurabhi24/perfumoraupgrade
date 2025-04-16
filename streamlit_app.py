import streamlit as st
import sqlite3
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch

# SQLite DB connection
def create_connection():
    conn = sqlite3.connect('perfume_app.db')
    return conn

# Function to initialize the database
def initialize_db():
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT)''')

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
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Username already exists.")
        conn.close()
        return False
    conn.close()
    return True

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
    cursor.execute("INSERT INTO history (user_id, preferences, recommendations) VALUES (?, ?, ?)", 
                   (user_id, preferences, recommendations))
    conn.commit()
    conn.close()

# Load the perfume dataset
def load_perfume_data():
    perfume_df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
    return perfume_df

# AI model for NLP-based recommendations
def get_recommendations(user_preferences, perfume_df):
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    perfume_df["combined"] = perfume_df["Description"].fillna("") + " " + perfume_df["Notes"].fillna("")
    
    user_input = " ".join(user_preferences)
    user_embedding = model.encode(user_input, convert_to_tensor=True)
    
    perfume_embeddings = model.encode(perfume_df["combined"].tolist(), convert_to_tensor=True)
    
    cosine_scores = util.pytorch_cos_sim(user_embedding, perfume_embeddings)[0]
    
    top_results = torch.topk(cosine_scores, k=5)
    
    recommended_perfumes = perfume_df.iloc[top_results[1]]
    
    return recommended_perfumes

# Show recommendations
def show_recommendations():
    preferences = st.session_state.answers
    mood = preferences.get("mood")
    occasion = preferences.get("occasion")
    notes = preferences.get("notes")

    perfume_df = load_perfume_data()

    user_preferences = [mood, occasion] + notes
    recommended_perfumes = get_recommendations(user_preferences, perfume_df)

    if not recommended_perfumes.empty:
        for _, row in recommended_perfumes.iterrows():
            description = row["Description"]
            highlighted_description = highlight_keywords(description, [mood, occasion] + notes)
            st.markdown(f"### *{row['Name']}* by {row['Brand']}")
            if pd.notna(row["Image URL"]):
                st.image(row["Image URL"], width=180)
            st.markdown(highlighted_description)
            st.markdown("---")
    else:
        st.error("No perfect match found. Try a different mood or notes!")

    user_id = st.session_state.user_id
    store_preferences(user_id, str(preferences), ", ".join(recommended_perfumes["Name"].head(5).tolist()))

    st.experimental_rerun()

# Registration page
def show_registration():
    st.title("Register a New Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Register"):
        if password == confirm_password:
            if register_user(username, password):
                st.success("Registration successful! Please log in.")
                st.session_state.logged_in = False
            else:
                st.error("Username already exists.")
        else:
            st.error("Passwords do not match.")

# Login page
def show_login():
    st.title("Login Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.logged_in = True
            st.session_state.answers = {}
            st.success("Login successful!")
            st.session_state.step = 1
            st.experimental_rerun()
        else:
            st.error("Invalid credentials, please try again.")

# Questionnaire for user preferences
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
            st.session_state.step = 4
            st.experimental_rerun()

# Main app routing logic
def main():
    initialize_db()
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    page = st.sidebar.radio("Choose a page", ["Login", "Register", "Questionnaire"])

    if page == "Login":
        if not st.session_state.logged_in:
            show_login()
        else:
            st.write(f"Hello {st.session_state.username}, you are already logged in.")
            show_questionnaire()

    elif page == "Register":
        show_registration()

    elif page == "Questionnaire":
        if st.session_state.logged_in:
            show_questionnaire()
        else:
            st.warning("Please log in first.")

if __name__ == "__main__":
    main()
