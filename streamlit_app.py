import streamlit as st
import sqlite3
import pandas as pd

# --- Session State Init ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {}

# --- SQLite Connection ---
def create_connection():
    conn = sqlite3.connect('perfume_app.db')
    return conn

# --- DB Table Creation (run once) ---
def initialize_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            preferences TEXT,
            recommendations TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

initialize_db()

# --- Register New User ---
def register_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Username already exists.")
    conn.close()

# --- Authenticate User ---
def authenticate_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# --- Store Preferences ---
def store_preferences(user_id, preferences, recommendations):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (user_id, preferences, recommendations) VALUES (?, ?, ?)", 
                   (user_id, preferences, recommendations))
    conn.commit()
    conn.close()

# --- Keyword Highlighting ---
def highlight_keywords(description, keywords):
    for keyword in keywords:
        description = description.replace(keyword, f"**{keyword}**")
    return description

# --- Recommendations Display ---
def show_recommendations():
    preferences = st.session_state.answers
    mood = preferences.get("mood")
    occasion = preferences.get("occasion")
    notes = preferences.get("notes")

    df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
    df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")

    query_keywords = [mood, occasion] + notes
    query_string = "|".join(query_keywords)

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

    user_id = st.session_state.user_id
    store_preferences(user_id, str(preferences), ", ".join(results["Name"].head(5).tolist()))

# --- Login Page ---
def show_login():
    st.title("Login Page")
    username = st.text_input("Username").strip()
    password = st.text_input("Password", type="password").strip()

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.logged_in = True
            st.session_state.step = 1
            st.session_state.answers = {}
            st.session_state.page = "Questionnaire"
            st.success("Login successful! Redirecting...")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials, please try again.")

    st.markdown("---")
    st.subheader("New here?")
    new_user = st.text_input("Create Username", key="new_user").strip()
    new_pass = st.text_input("Create Password", type="password", key="new_pass").strip()
    if st.button("Register"):
        if new_user and new_pass:
            register_user(new_user, new_pass)
            st.success("Account created! You can now log in.")
        else:
            st.error("Username and password cannot be empty.")

# --- Questionnaire Steps ---
def show_questionnaire():
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
        st.subheader("Your Personalized Perfume Picks ✨")
        show_recommendations()

# --- Database Viewer ---
def view_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM history")
    history = cursor.fetchall()
    conn.close()

    st.subheader("Users Table:")
    st.write(users)
    
    st.subheader("History Table:")
    st.write(history)

# --- Logout Option ---
def logout():
    st.session_state.logged_in = False
    st.session_state.page = "Login"
    st.success("Logged out successfully.")
    st.experimental_rerun()

# --- Routing ---
if __name__ == "__main__":
    if st.session_state.logged_in:
        st.session_state.page = "Questionnaire"

    if st.session_state.logged_in:
        with st.sidebar:
            st.write(f"👤 Logged in as: **{st.session_state.username}**")
            if st.button("Logout"):
                logout()

    page = st.sidebar.radio("Choose a page", ["Login", "Questionnaire", "View Database"], 
                            index=["Login", "Questionnaire", "View Database"].index(st.session_state.page))

    if page == "Login":
        show_login()
    elif page == "Questionnaire":
        if not st.session_state.logged_in:
            st.warning("Please login first.")
            show_login()
        else:
            show_questionnaire()
    elif page == "View Database":
        view_db()
