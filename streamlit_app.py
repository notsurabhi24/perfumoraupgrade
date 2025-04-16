import streamlit as st
import sqlite3
import pandas as pd

# SQLite connection
def create_connection():
    conn = sqlite3.connect("perfume_app.db")
    return conn

# Setup DB tables if not exist
def setup_database():
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
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Register a new user
def register_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

# Authenticate user
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

# Highlight words
def highlight_keywords(description, keywords):
    for keyword in keywords:
        if keyword:
            description = description.replace(keyword, f"**{keyword}**")
    return description

# Show recommendations
def show_recommendations():
    preferences = st.session_state.answers
    mood = preferences.get("mood")
    occasion = preferences.get("occasion")
    notes = preferences.get("notes")

    df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
    df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")
    query_keywords = [mood, occasion] + notes
    query_string = "|".join([kw for kw in query_keywords if kw])
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
        st.error("No match found. Try changing the mood or notes!")

    store_preferences(st.session_state.user_id, str(preferences), ", ".join(results["Name"].head(5).tolist()))

# Login page
def show_login():
    if st.session_state.get("logged_in"):
        st.session_state.page = "Questionnaire"
        st.experimental_rerun()

    st.title("🌸 Perfume Recommender - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.logged_in = True
            st.session_state.page = "Questionnaire"
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")

    if st.button("Register"):
        if username and password:
            try:
                register_user(username, password)
                st.success("Registration successful. Please login.")
            except:
                st.error("Username already exists.")
        else:
            st.warning("Please fill both fields.")

# Questionnaire flow
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
        show_recommendations()

# DB Viewer (for debug)
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

# Main router
def main():
    setup_database()
    if "page" not in st.session_state:
        st.session_state.page = "Login"

    if st.session_state.page == "Login":
        show_login()
    elif st.session_state.page == "Questionnaire":
        show_questionnaire()
    elif st.session_state.page == "View Database":
        view_db()

# Run the app
if __name__ == "__main__":
    main()
