import streamlit as st
import sqlite3
import pandas as pd

# Function to create connection to the SQLite database
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

# Function to check if the user exists and their password is correct
def validate_user(username, password):
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

# Function to load perfume data
def load_perfume_data():
    df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
    df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")
    return df

# Streamlit app

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# Page routing for the questionnaire
def show_questionnaire():
    df = load_perfume_data()

    # Step 1: Mood
    if st.session_state.step == 1:
        st.subheader("Step 1: What's your current vibe?")
        mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
        if st.button("Next ➡"):
            st.session_state.answers["mood"] = mood
            st.session_state.step = 2

    # Step 2: Occasion
    elif st.session_state.step == 2:
        st.subheader("Step 2: What's the occasion?")
        occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])
        if st.button("Next ➡"):
            st.session_state.answers["occasion"] = occasion
            st.session_state.step = 3

    # Step 3: Notes
    elif st.session_state.step == 3:
        st.subheader("Step 3: What kind of notes do you love?")
        notes = st.multiselect("Pick a few that speak to your soul 💫", 
                               ["Vanilla", "Oud", "Citrus", "Floral", "Spicy", "Woody", "Sweet", "Musky"])
        if st.button("Get My Recommendations 💖"):
            st.session_state.answers["notes"] = notes
            st.session_state.step = 4

    # Step 4: Results
    elif st.session_state.step == 4:
        st.subheader("💐 Based on your vibe, you might love these:")

        mood = st.session_state.answers["mood"]
        occasion = st.session_state.answers["occasion"]
        notes = st.session_state.answers["notes"]

        # Search using keywords in the combined column
        query_keywords = [mood, occasion] + notes
        query_string = "|".join(query_keywords)

        # Perform the search for matches in the combined column
        results = df[df["combined"].str.contains(query_string, case=False, na=False)]

        recommendations = []
        if not results.empty:
            for _, row in results.head(5).iterrows():
                st.markdown(f"### *{row['Name']}* by {row['Brand']}")
                if pd.notna(row["Image URL"]):
                    st.image(row["Image URL"], width=180)
                st.write(row["Description"])
                recommendations.append(row['Name'])
                st.markdown("---")
        else:
            st.error("No perfect match found 😢 Try a different mood or notes!")

        # Store preferences and recommendations in database
        user_id = st.session_state.user_id
        preferences = f"Mood: {mood}, Occasion: {occasion}, Notes: {', '.join(notes)}"
        store_preferences(user_id, preferences, ", ".join(recommendations))

        if st.button("🔄 Start Over"):
            st.session_state.step = 1
            st.session_state.answers = {}

# Main page

# Login page
def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = validate_user(username, password)
        if user:
            st.session_state.user_id = user[0]  # User ID is stored in session state
            st.session_state.step = 1  # Start questionnaire
            st.success("Login successful! Redirecting to questionnaire...")
        else:
            st.error("Invalid username or password")

# Registration page
def register_page():
    st.title("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        register_user(username, password)
        st.success("Registration successful! You can now log in.")

# Sidebar navigation
page = st.sidebar.selectbox("Select page", ["Login", "Register", "Questionnaire"])

if page == "Login":
    login_page()
elif page == "Register":
    register_page()
elif page == "Questionnaire":
    show_questionnaire()
