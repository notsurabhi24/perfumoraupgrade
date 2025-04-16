import streamlit as st
import sqlite3
import pandas as pd
import os

# Ensure database and tables exist
def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            preferences TEXT,
            recommendations TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# SQLite DB connection
def create_connection():
    return sqlite3.connect('perfume_app.db')

# Function to register a new user
def register_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Username already exists. Try another.")
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

# Highlight keywords in descriptions
def highlight_keywords(description, keywords):
    if not description:
        return ""
    for keyword in keywords:
        description = description.replace(keyword, f"**{keyword}**")
    return description

# Show perfume recommendations
def show_recommendations():
    preferences = st.session_state.get("answers", {})
    mood = preferences.get("mood")
    occasion = preferences.get("occasion")
    notes = preferences.get("notes", [])

    df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
    df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")

    query_keywords = [mood, occasion] + notes
    query_string = "|".join([q for q in query_keywords if q])

    results = df[df["combined"].str.contains(query_string, case=False, na=False)]

    if not results.empty:
        for _, row in results.head(5).iterrows():
            description = row["Description"]
            highlighted = highlight_keywords(description, query_keywords)
            st.markdown(f"### *{row['Name']}* by {row['Brand']}")
            if pd.notna(row["Image URL"]):
                st.image(row["Image URL"], width=180)
            st.markdown(highlighted)
            st.markdown("---")
    else:
        st.error("No perfect match found 😢 Try a different mood or notes!")

    user_id = st.session_state.get("user_id")
    if user_id:
        store_preferences(user_id, str(preferences), ", ".join(results["Name"].head(5).tolist()))

# Show login screen
def show_login():
    st.title("🌸 Perfume Recommender - Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.logged_in = True
            st.session_state.step = 1
            st.session_state.answers = {}
            st.success("Login successful! Redirecting...")
            st.session_state.page = "Questionnaire"
            st.experimental_rerun()
        else:
            st.error("Invalid credentials, please try again.")

    if st.button("Register"):
        if username and password:
            register_user(username, password)
            st.success("User registered. Please log in.")
        else:
            st.warning("Enter both username and password.")

# Questionnaire workflow
def show_questionnaire():
    st.title("💐 Find Your Signature Scent")
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'answers' not in st.session_state:
        st.session_state.answers = {}

    if st.session_state.step == 1:
        st.subheader("Step 1: What's your current vibe?")
        mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
        if st.button("Next ➡️"):
            st.session_state.answers["mood"] = mood
            st.session_state.step = 2
            st.experimental_rerun()

    elif st.session_state.step == 2:
        st.subheader("Step 2: What's the occasion?")
        occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])
        if st.button("Next ➡️"):
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
        show_recommendations()

# View database (debugging/admin)
def view_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM history")
    history = cursor.fetchall()
    conn.close()

    st.subheader("👥 Users Table:")
    st.write(users)

    st.subheader("📜 History Table:")
    st.write(history)

# Main routing logic
def main():
    create_tables()

    if "page" not in st.session_state:
        st.session_state.page = "Login"

    page = st.sidebar.radio("Navigation", ["Login", "Questionnaire", "View Database"])

    if page == "Login":
        show_login()
    elif page == "Questionnaire":
        if st.session_state.get("logged_in"):
            show_questionnaire()
        else:
            st.warning("Please log in first.")
            show_login()
    elif page == "View Database":
        view_db()

if __name__ == "__main__":
    main()
