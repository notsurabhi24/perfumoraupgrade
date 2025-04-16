import streamlit as st
import sqlite3
import pandas as pd

# Create and connect to the SQLite DB
def create_connection():
    conn = sqlite3.connect('perfume_app.db')
    return conn

# Set up DB tables if they don't exist
def setup_database():
    conn = create_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            preferences TEXT,
            recommendations TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

# Call this at the top so it runs when the app starts
setup_database()

# Register user
def register_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Username already exists.")
    conn.close()

# Authenticate user
def authenticate_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Store user preferences and recommendations
def store_preferences(user_id, preferences, recommendations):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (user_id, preferences, recommendations) VALUES (?, ?, ?)", 
                   (user_id, preferences, recommendations))
    conn.commit()
    conn.close()

# Highlight keywords in perfume description
def highlight_keywords(description, keywords):
    for keyword in keywords:
        description = description.replace(keyword, f"**{keyword}**")
    return description

# Show perfume recommendations
def show_recommendations():
    preferences = st.session_state.answers
    mood = preferences.get("mood")
    occasion = preferences.get("occasion")
    notes = preferences.get("notes", [])

    df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
    df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")

    query_keywords = [mood, occasion] + notes
    query_string = "|".join(query_keywords)

    results = df[df["combined"].str.contains(query_string, case=False, na=False)]

    if not results.empty:
        for _, row in results.head(5).iterrows():
            description = row["Description"]
            highlighted_description = highlight_keywords(description, query_keywords)
            st.markdown(f"### *{row['Name']}* by {row['Brand']}")
            if pd.notna(row["Image URL"]):
                st.image(row["Image URL"], width=180)
            st.markdown(highlighted_description)
            st.markdown("---")
    else:
        st.error("No perfect match found 😢 Try a different mood or notes!")

    user_id = st.session_state.get("user_id")
    if user_id:
        store_preferences(user_id, str(preferences), ", ".join(results["Name"].head(5).tolist()))
        st.success("Your preferences were saved!")
    
    st.experimental_rerun()

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
            st.experimental_rerun()
        else:
            st.error("Invalid credentials, please try again.")

    st.markdown("Don't have an account?")
    new_user = st.text_input("Create Username", key="new_user")
    new_pass = st.text_input("Create Password", type="password", key="new_pass")
    if st.button("Register"):
        if new_user and new_pass:
            register_user(new_user, new_pass)
            st.success("Account created! Please log in.")
        else:
            st.error("Username and password cannot be empty.")

# Questionnaire logic
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

# View database contents
def view_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM history")
    history = cursor.fetchall()
    conn.close()

    st.subheader("Users Table:")
    st.write(pd.DataFrame(users, columns=["ID", "Username", "Password"]))
    
    st.subheader("History Table:")
    st.write(pd.DataFrame(history, columns=["ID", "User ID", "Preferences", "Recommendations"]))

# App routing
if __name__ == "__main__":
    page = st.sidebar.radio("Choose a page", ["Login", "Questionnaire", "View Database"])
    
    if page == "Login":
        show_login()
    elif page == "Questionnaire":
        show_questionnaire()
    elif page == "View Database":
        view_db()
