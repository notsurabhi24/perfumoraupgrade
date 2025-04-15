import streamlit as st
import pandas as pd
import hashlib
import bcrypt

# Load the users and history CSV files (if they exist)
try:
    users_df = pd.read_csv("users.csv")
except FileNotFoundError:
    users_df = pd.DataFrame(columns=["username", "password", "email"])

try:
    history_df = pd.read_csv("history.csv")
except FileNotFoundError:
    history_df = pd.DataFrame(columns=["username", "history"])

# Function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Function to check if the password is correct
def check_password(stored_password, input_password):
    return bcrypt.checkpw(input_password.encode('utf-8'), stored_password.encode('utf-8'))

# Register the user
def register_user(username, password, email):
    global users_df, history_df
    if username in users_df['username'].values:
        return False  # User already exists
    hashed_pw = hash_password(password)
    new_user = pd.DataFrame({"username": [username], "password": [hashed_pw], "email": [email]})
    users_df = pd.concat([users_df, new_user], ignore_index=True)
    users_df.to_csv("users.csv", index=False)
    # Create initial history entry for the user
    history_data = pd.DataFrame({"username": [username], "history": ['']})
    history_df = pd.concat([history_df, history_data], ignore_index=True)
    history_df.to_csv("history.csv", index=False)
    return True

# Save the user's answers and recommended perfumes into the history
def save_user_history(username, answers, recommended_perfumes):
    global history_df
    history_data = {
        "username": username,
        "history": f"Answers: {answers}, Recommended: {recommended_perfumes}"
    }
    history_df = history_df.append(history_data, ignore_index=True)
    history_df.to_csv("history.csv", index=False)

# App title
st.set_page_config(page_title="Perfume Matchmaker", layout="centered")
st.title("🌸 Perfume Personality Matchmaker")

# Session state init
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# Switch between Registration and Login pages
def login_page():
    if not st.session_state.user_logged_in:
        login_or_register = st.radio("Login or Register", ["Login", "Register"])
        
        if login_or_register == "Login":
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if username in users_df['username'].values:
                    user_data = users_df[users_df["username"] == username].iloc[0]
                    if check_password(user_data['password'], password):
                        st.session_state.user_logged_in = True
                        st.session_state.username = username
                        st.success("Logged in successfully!")
                    else:
                        st.error("Incorrect password.")
                else:
                    st.error("User does not exist.")
        
        elif login_or_register == "Register":
            st.subheader("Register")
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.button("Register"):
                if password == confirm_password:
                    if register_user(username, password, email):
                        st.session_state.user_logged_in = True
                        st.session_state.username = username
                        st.success("Registered and logged in successfully!")
                    else:
                        st.error("Username already exists.")
                else:
                    st.error("Passwords do not match.")
    else:
        st.write(f"Logged in as {st.session_state.username}")
        st.button("Logout", on_click=logout)

# Logout function
def logout():
    st.session_state.user_logged_in = False
    st.session_state.username = ""
    st.session_state.answers = {}
    st.session_state.step = 1

# Main logic for perfume recommendations (steps from your previous code)
def perfume_recommender():
    if st.session_state.user_logged_in:
        if st.session_state.step == 1:
            st.subheader("Step 1: What's your current vibe?")
            mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
            if st.button("Next ➡️"):
                st.session_state.answers["mood"] = mood
                st.session_state.step += 1

        elif st.session_state.step == 2:
            st.subheader("Step 2: What's the occasion?")
            occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])
            if st.button("Next ➡️"):
                st.session_state.answers["occasion"] = occasion
                st.session_state.step += 1

        elif st.session_state.step == 3:
            st.subheader("Step 3: What kind of notes do you love?")
            notes = st.multiselect("Pick a few that speak to your soul 💫", 
                                ["Vanilla", "Oud", "Citrus", "Floral", "Spicy", "Woody", "Sweet", "Musky"])
            if st.button("Get My Recommendations 💖"):
                st.session_state.answers["notes"] = notes
                st.session_state.step += 1

        elif st.session_state.step == 4:
            st.subheader("💐 Based on your vibe, you might love these:")
            
            mood = st.session_state.answers["mood"]
            occasion = st.session_state.answers["occasion"]
            notes = st.session_state.answers["notes"]
            
            query_keywords = [mood, occasion] + notes
            query_string = "|".join(query_keywords)
            
            # Filter the perfumes based on the query
            df
