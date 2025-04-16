import streamlit as st
import sqlite3
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# Load NLP model
model = SentenceTransformer('all-MiniLM-L6-v2')

# SQLite DB connection
def create_connection():
    conn = sqlite3.connect('perfume_app.db')
    return conn

# Create necessary tables if they don't exist
def initialize_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            preferences TEXT,
            recommendations TEXT
        )
    """)
    conn.commit()
    conn.close()

# Register a new user
def register_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        st.success("Registration successful!")
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose another.")
    conn.close()

# Authenticate a user
def authenticate_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Store preferences
def store_preferences(user_id, preferences, recommendations):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (user_id, preferences, recommendations) VALUES (?, ?, ?)", 
                   (user_id, preferences, recommendations))
    conn.commit()
    conn.close()

# NLP-based recommendation system
def get_ai_recommendations(preferences):
    mood = preferences.get("mood", "")
    occasion = preferences.get("occasion", "")
    notes = preferences.get("notes", [])
    
    user_input = f"{mood} {occasion} {' '.join(notes)}"
    input_embedding = model.encode(user_input, convert_to_tensor=True)

    df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
    df['combined'] = df['Description'].fillna('') + " " + df['Notes'].fillna('')
    df['embedding'] = df['combined'].apply(lambda x: model.encode(x, convert_to_tensor=True))
    df['score'] = df['embedding'].apply(lambda x: util.pytorch_cos_sim(x, input_embedding).item())
    df = df.sort_values(by="score", ascending=False)

    return df.head(5)

# Highlight preferred words
def highlight_keywords(description, keywords):
    for keyword in keywords:
        description = description.replace(keyword, f"**{keyword}**")
    return description

# Show recommendations
def show_recommendations():
    preferences = st.session_state.answers
    top_results = get_ai_recommendations(preferences)

    st.subheader("Your Personalized Picks 💖")

    for _, row in top_results.iterrows():
        st.markdown(f"### *{row['Name']}* by {row['Brand']}")
        if pd.notna(row["Image URL"]):
            st.image(row["Image URL"], width=180)
        description = row["Description"] or ""
        st.markdown(highlight_keywords(description, [preferences['mood'], preferences['occasion']] + preferences['notes']))
        st.markdown("---")

    store_preferences(
        st.session_state.user_id, 
        str(preferences), 
        ", ".join(top_results["Name"].tolist())
    )

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
            st.session_state.step = 1
            st.session_state.answers = {}
            st.success("Login successful! Redirecting to quiz...")
            st.session_state.logged_in = True
            st.experimental_rerun()  # Now works after login
        else:
            st.error("Invalid credentials.")

# Registration page
def show_registration():
    st.title("Registration Page")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if password == confirm_password:
            register_user(username, password)
        else:
            st.error("Passwords do not match. Please try again.")

# Questionnaire page
def show_questionnaire():
    step = st.session_state.get("step", 1)

    if step == 1:
        st.subheader("Step 1: What's your current vibe?")
        mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
        if st.button("Next ➡"):
            st.session_state.answers["mood"] = mood
            st.session_state.step = 2
            st.experimental_rerun()

    elif step == 2:
        st.subheader("Step 2: What's the occasion?")
        occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])
        if st.button("Next ➡"):
            st.session_state.answers["occasion"] = occasion
            st.session_state.step = 3
            st.experimental_rerun()

    elif step == 3:
        st.subheader("Step 3: What kind of notes do you love?")
        notes = st.multiselect("Pick your fav scent notes 💫", 
                               ["Vanilla", "Oud", "Citrus", "Floral", "Spicy", "Woody", "Sweet", "Musky"])
        if st.button("Get My Recommendations 💖"):
            st.session_state.answers["notes"] = notes
            st.session_state.step = 4
            st.experimental_rerun()

    elif step == 4:
        show_recommendations()

# View DB (debug)
def view_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM history")
    history = cursor.fetchall()
    conn.close()
    st.subheader("Users Table")
    st.write(users)
    st.subheader("History Table")
    st.write(history)

# Routing logic
def main():
    initialize_db()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    page = st.sidebar.radio("Choose a page", ["Login", "Register", "Questionnaire", "View Database"])

    if page == "Login":
        if st.session_state.logged_in:
            show_questionnaire()
        else:
            show_login()

    elif page == "Register":
        show_registration()

    elif page == "Questionnaire":
        if st.session_state.logged_in:
            show_questionnaire()
        else:
            st.warning("Please login first.")

    elif page == "View Database":
        view_db()

if __name__ == "__main__":
    main()
