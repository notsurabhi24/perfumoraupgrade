import streamlit as st
import pandas as pd
import sqlite3
from sentence_transformers import SentenceTransformer, util

# Initialize SentenceTransformer for NLP (You can train or load your custom model here)
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# SQLite DB connection
def create_connection():
    conn = sqlite3.connect('perfume_app.db')
    return conn

# Function to create the necessary tables in the database
def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        username TEXT, 
                        password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        user_id INTEGER,
                        preferences TEXT, 
                        recommendations TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id))''')
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
    cursor.execute("INSERT INTO history (user_id, preferences, recommendations) VALUES (?, ?, ?)", 
                   (user_id, preferences, recommendations))
    conn.commit()
    conn.close()

# Dummy AI model (replace with real NLP model)
def get_recommendations(preferences):
    df = pd.read_csv('final_perfume_data.csv', encoding="ISO-8859-1")
    mood = preferences.get('mood')
    if mood:
        # Simulating AI model logic, ideally you'd match the mood with perfumes in the CSV
        recommendations = df[df['Description'].str.contains(mood, case=False, na=False)]
        return recommendations.head(5)
    return pd.DataFrame()  # Return empty if no recommendations

# Function to highlight keywords in the perfume description
def highlight_keywords(description, keywords):
    for keyword in keywords:
        description = description.replace(keyword, f"**{keyword}**")
    return description

# Show recommendations with highlighted preferences
def show_recommendations(preferences):
    results = get_recommendations(preferences)
    if not results.empty:
        for _, row in results.iterrows():
            description = row['Description']
            highlighted_description = highlight_keywords(description, [preferences.get("mood", "")])
            st.markdown(f"### *{row['Name']}* by {row['Brand']}")
            st.markdown(highlighted_description)
            st.markdown("---")
    else:
        st.error("No matching recommendations found.")

# Show login page
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
            st.success("Login successful!")
            st.experimental_rerun()  # Redirect to questionnaire
        else:
            st.error("Invalid credentials, please try again.")

# Show registration page
def show_register():
    st.title("Register Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Register"):
        register_user(username, password)
        st.success("Registration successful! You can now log in.")

# Show the questionnaire
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

    elif st.session_state.step == 4:
        st.subheader("Here are your recommendations!")
        show_recommendations(st.session_state.answers)

        # Store preferences and recommendations in the database
        store_preferences(st.session_state.user_id, str(st.session_state.answers), 
                          ", ".join(st.session_state.answers.get("mood", [])))
        st.success("Preferences saved to history.")

# Main app routing logic
def main():
    create_tables()  # Ensure tables are created on startup

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        page = st.sidebar.radio("Choose a page", ["Login", "Register"])
        if page == "Login":
            show_login()
        elif page == "Register":
            show_register()
    else:
        show_questionnaire()

if __name__ == "__main__":
    main()
