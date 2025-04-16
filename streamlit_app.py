import streamlit as st
import pandas as pd
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Database connection setup
def create_connection():
    conn = sqlite3.connect('perfume_app.db')
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        mood TEXT,
        occasion TEXT,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

# Create tables if they don't exist
create_table()

# Load dataset
df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")

# Combine text for searching using the correct column names
df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")

# Session state init
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# Login and registration functions
def register_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone() is not None:
        return "Username already exists."
    hashed_pw = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
    conn.commit()
    conn.close()
    return "User registered successfully!"

def authenticate_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    record = cursor.fetchone()
    conn.close()
    if record and check_password_hash(record[0], password):
        return True
    return False

# App title
st.set_page_config(page_title="Perfume Matchmaker", layout="centered")
st.title("🌸 Perfume Personality Matchmaker")
st.markdown("Let your vibes choose your scent. Answer a few questions and we'll match you with your signature fragrance!")

# Login page
def show_login():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials, please try again.")

# Register page
def show_register():
    st.subheader("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Register"):
        result = register_user(username, password)
        st.success(result)

# Step 1 – Mood
if 'logged_in' not in st.session_state:
    page = st.sidebar.radio("Choose a page", ["Login", "Register"])
    if page == "Login":
        show_login()
    elif page == "Register":
        show_register()
elif st.session_state.logged_in:
    # Proceed with questionnaire if logged in
    if st.session_state.step == 1:
        st.subheader("Step 1: What's your current vibe?")
        mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
        if st.button("Next ➡"):
            st.session_state.answers["mood"] = mood
            st.session_state.step = 2  # Move to next step directly

    elif st.session_state.step == 2:
        st.subheader("Step 2: What's the occasion?")
        occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])
        if st.button("Next ➡"):
            st.session_state.answers["occasion"] = occasion
            st.session_state.step = 3  # Move to next step

    elif st.session_state.step == 3:
        st.subheader("Step 3: What kind of notes do you love?")
        notes = st.multiselect("Pick a few that speak to your soul 💫", 
                               ["Vanilla", "Oud", "Citrus", "Floral", "Spicy", "Woody", "Sweet", "Musky"])
        if st.button("Get My Recommendations 💖"):
            st.session_state.answers["notes"] = notes
            st.session_state.step = 4  # Proceed to results after getting notes

    elif st.session_state.step == 4:
        st.subheader("💐 Based on your vibe, you might love these:")

        mood = st.session_state.answers["mood"]
        occasion = st.session_state.answers["occasion"]
        notes = st.session_state.answers["notes"]

        # Search using keywords in the combined text
        query_keywords = [mood, occasion] + notes
        query_string = "|".join(query_keywords)

        # Perform the search for matches in the combined column
        results = df[df["combined"].str.contains(query_string, case=False, na=False)]

        if not results.empty:
            for _, row in results.head(5).iterrows():
                st.markdown(f"### *{row['Name']}* by {row['Brand']}")
                if pd.notna(row["Image URL"]):
                    st.image(row["Image URL"], width=180)
                st.write(row["Description"])
                st.markdown("---")
        else:
            st.error("No perfect match found 😢 Try a different mood or notes!")

        # Save the recommendation in the database
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (st.session_state.username,))
        user_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO recommendations (user_id, mood, occasion, notes) VALUES (?, ?, ?, ?)",
                       (user_id, mood, occasion, ", ".join(notes)))
        conn.commit()
        conn.close()

        if st.button("🔄 Start Over"):
            st.session_state.step = 1
            st.session_state.answers = {}
