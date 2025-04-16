import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset
df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")

# Combine text for searching using the correct column names
df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")

# Session state init
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'history' not in st.session_state:
    st.session_state.history = {}

# Function to save the user's answers to history
def save_to_history(username, answers):
    if username not in st.session_state.history:
        st.session_state.history[username] = []
    st.session_state.history[username].append(answers)

# Function to register a new user
def register_user(username, password):
    if username in st.session_state.user_data:
        st.error("Username already exists!")
    else:
        st.session_state.user_data[username] = password
        st.success("Registration successful! Please log in.")

# Function to login a user
def login_user(username, password):
    if username not in st.session_state.user_data:
        st.error("Username does not exist.")
    elif st.session_state.user_data[username] != password:
        st.error("Incorrect password.")
    else:
        st.success(f"Welcome back, {username}!")
        return True
    return False

# Registration and Login Page
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.subheader("Login / Register")
    option = st.sidebar.radio("Choose an option", ["Login", "Register", "View History"])

    if option == "Register":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Register"):
            register_user(username, password)

    if option == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username

    if option == "View History":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login to View History"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                user_history = st.session_state.history.get(st.session_state.username, [])
                if user_history:
                    st.sidebar.subheader("Your History")
                    for entry in user_history:
                        st.sidebar.write(entry)
                else:
                    st.sidebar.write("No history found.")
else:
    # Perfume Recommendation App for logged-in users
    st.set_page_config(page_title="Perfume Matchmaker", layout="centered")
    st.title("🌸 Perfume Personality Matchmaker")
    st.markdown("Let your vibes choose your scent. Answer a few questions and we'll match you with your signature fragrance!")

    # Displaying User's History if Logged In
    if 'username' in st.session_state:
        user_history = st.session_state.history.get(st.session_state.username, [])
        if user_history:
            st.sidebar.subheader("Your History")
            for entry in user_history:
                st.sidebar.write(entry)
        else:
            st.sidebar.write("No history found.")

    # Step 1 – Mood
    if st.session_state.step == 1:
        st.subheader("Step 1: What's your current vibe?")
        mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
        if st.button("Next ➡"):
            st.session_state.answers["mood"] = mood
            st.session_state.step = 2  # Move to next step directly

    # Step 2 – Occasion
    elif st.session_state.step == 2:
        st.subheader("Step 2: What's the occasion?")
        occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])
        if st.button("Next ➡"):
            st.session_state.answers["occasion"] = occasion
            st.session_state.step = 3  # Move to next step

    # Step 3 – Notes
    elif st.session_state.step == 3:
        st.subheader("Step 3: What kind of notes do you love?")
        notes = st.multiselect("Pick a few that speak to your soul 💫", 
                               ["Vanilla", "Oud", "Citrus", "Floral", "Spicy", "Woody", "Sweet", "Musky"])
        if st.button("Get My Recommendations 💖"):
            st.session_state.answers["notes"] = notes
            st.session_state.step = 4  # Proceed to results after getting notes

    # Step 4 – Results (NLP Model)
    elif st.session_state.step == 4:
        st.subheader("💐 Based on your vibe, you might love these:")

        mood = st.session_state.answers["mood"]
        occasion = st.session_state.answers["occasion"]
        notes = st.session_state.answers["notes"]

        # Search using keywords in the combined column
        query_keywords = [mood, occasion] + notes
        query_string = "|".join(query_keywords)

        # Perform the search for matches in the combined column
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(df['combined'])
        query_tfidf = vectorizer.transform([query_string])
        cosine_sim = cosine_similarity(query_tfidf, tfidf_matrix)

        top_matches = cosine_sim[0].argsort()[-5:][::-1]

        if top_matches.size > 0:
            for idx in top_matches:
                row = df.iloc[idx]
                st.markdown(f"### *{row['Name']}* by {row['Brand']}")
                if pd.notna(row["Image URL"]):
                    st.image(row["Image URL"], width=180)
                st.write(row["Description"])
                st.markdown("---")
        else:
            st.error("No perfect match found 😢 Try a different mood or notes!")

        # Save to history for logged-in users
        if 'username' in st.session_state:
            save_to_history(st.session_state.username, st.session_state.answers)

        if st.button("🔄 Start Over"):
            st.session_state.step = 1
            st.session_state.answers = {}
