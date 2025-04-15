import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Ensure CSV files exist
if not os.path.exists("users.csv"):
    pd.DataFrame(columns=["username", "password"]).to_csv("users.csv", index=False)

if not os.path.exists("history.csv"):
    pd.DataFrame(columns=["username", "recommendation", "date"]).to_csv("history.csv", index=False)

# Function to register a new user
def register_user(username, password):
    users = pd.read_csv("users.csv")
    if username not in users['username'].values:
        users = users.append({"username": username, "password": password}, ignore_index=True)
        users.to_csv("users.csv", index=False)
        return True
    else:
        return False

# Function to login a user
def login_user(username, password):
    users = pd.read_csv("users.csv")
    user = users[users['username'] == username]
    if not user.empty and user['password'].values[0] == password:
        return True
    else:
        return False

# Function to save history of user recommendations
def save_history(username, recommendation):
    history = pd.read_csv("history.csv")
    history = history.append({"username": username, "recommendation": recommendation, "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, ignore_index=True)
    history.to_csv("history.csv", index=False)

# Streamlit UI for registration/login
def login_register_page():
    st.title("Perfume Personality Matchmaker")
    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Select Activity", menu)

    # Registration page
    if choice == "Register":
        st.subheader("Create a New Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if password == confirm_password:
                if register_user(username, password):
                    st.success(f"Account created for {username}")
                else:
                    st.warning("Username already exists.")
            else:
                st.warning("Passwords do not match.")

    # Login page
    elif choice == "Login":
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if login_user(username, password):
                st.success(f"Welcome {username}")
                st.session_state.username = username
                questionnaire_page(username)
            else:
                st.warning("Invalid username or password.")

# Questionnaire page after login
def questionnaire_page(username):
    # Load dataset
    df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
    df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")
    
    # Session state init
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'answers' not in st.session_state:
        st.session_state.answers = {}

    # App title
    st.set_page_config(page_title="Perfume Matchmaker", layout="centered")
    st.title("🌸 Perfume Personality Matchmaker")
    st.markdown("Let your vibes choose your scent. Answer a few questions and we'll match you with your signature fragrance!")

    # Step 1 – Mood
    if st.session_state.step == 1:
        st.subheader("Step 1: What's your current vibe?")
        mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
        if st.button("Next ➡"):
            st.session_state.answers["mood"] = mood
            st.session_state.step = 2  # Move to next step

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
            st.session_state.step = 4  # Proceed to results

    # Step 4 – Results
    elif st.session_state.step == 4:
        st.subheader("💐 Based on your vibe, you might love these:")

        mood = st.session_state.answers["mood"]
        occasion = st.session_state.answers["occasion"]
        notes = st.session_state.answers["notes"]

        # Combine user's selections into a single list of keywords
        user_keywords = [mood, occasion] + notes

        # Search using keywords in the combined column
        query_keywords = [mood, occasion] + notes
        query_string = "|".join(query_keywords)

        # Perform the search for matches in the combined column
        results = df[df["combined"].str.contains(query_string, case=False, na=False)]

        if not results.empty:
            for _, row in results.head(5).iterrows():
                st.markdown(f"### *{row['Name']}* by {row['Brand']}")
                
                if pd.notna(row["Image URL"]):
                    st.image(row["Image URL"], width=180)

                # Highlight keywords in the description
                description = row["Description"]
                for keyword in user_keywords:
                    description = description.replace(keyword, f"<mark>{keyword}</mark>")
                
                # Print the highlighted description
                st.markdown(description, unsafe_allow_html=True)

                st.markdown("---")

            # Save the history of recommendations
            recommendation = f"Fragrance recommendations for {mood}, {occasion} with notes {', '.join(notes)}."
            save_history(username, recommendation)

        else:
            st.error("No perfect match found 😢 Try a different mood or notes!")

        if st.button("🔄 Start Over"):
            st.session_state.step = 1
            st.session_state.answers = {}

# Main entry point
if __name__ == "__main__":
    login_register_page()
