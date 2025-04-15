import streamlit as st
import sqlite3
import pandas as pd

# SQLite DB connection
def create_connection():
    conn = sqlite3.connect('perfume_app.db')
    return conn

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
    
    # Check if user exists in the users table
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        # Store preferences and recommendations in the history table
        cursor.execute("INSERT INTO history (user_id, preferences, recommendations) VALUES (?, ?, ?)", 
                       (user_id, preferences, recommendations))
        conn.commit()
    conn.close()

# Function to highlight the preferred words in the description
def highlight_keywords(description, keywords):
    for keyword in keywords:
        description = description.replace(keyword, f"**{keyword}**")
    return description

# Show recommendations with highlighted preferences
def show_recommendations():
    # Assuming the user's answers are stored in session state
    preferences = st.session_state.answers
    mood = preferences.get("mood")
    occasion = preferences.get("occasion")
    notes = preferences.get("notes")

    # Search in the perfume dataset
    df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
    df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")
    
    query_keywords = [mood, occasion] + notes
    query_string = "|".join(query_keywords)

    results = df[df["combined"].str.contains(query_string, case=False, na=False)]

    if not results.empty:
        for _, row in results.head(5).iterrows():
            description = row["Description"]
            highlighted_description = highlight_keywords(description, [mood, occasion] + notes)
            st.markdown(f"### *{row['Name']}* by {row['Brand']}")
            if pd.notna(row["Image URL"]):
                st.image(row["Image URL"], width=180)
            st.markdown(highlighted_description)
            st.markdown("---")
    else:
        st.error("No perfect match found 😢 Try a different mood or notes!")

    # Store preferences and recommendations
    user_id = st.session_state.user_id  # Assuming this is already set in the session state
    store_preferences(user_id, str(preferences), ", ".join(results["Name"].head(5).tolist()))

    # Redirect back to the questionnaire after a delay
    st.experimental_rerun()

# Page layout and routing
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
            st.experimental_rerun()  # Redirect to the questionnaire
        else:
            st.error("Invalid credentials, please try again.")

def show_questionnaire():
    # Questionnaire steps using session state to keep track of progress
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

# Show the SQLite database contents (for debugging/viewing data)
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

# Main app routing logic
if __name__ == "__main__":
    page = st.sidebar.radio("Choose a page", ["Login", "Questionnaire", "View Database"])
    
    if page == "Login":
        show_login()
    elif page == "Questionnaire":
        show_questionnaire()
    elif page == "View Database":
        view_db()
