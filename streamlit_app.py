import streamlit as st
import pandas as pd
import bcrypt
import os
from datetime import datetime

# ---------------- File Setup ----------------
USER_FILE = "users.csv"
HISTORY_FILE = "history.csv"
DATA_FILE = "final_perfume_data.csv"

if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["username", "password_hash"]).to_csv(USER_FILE, index=False)

if not os.path.exists(HISTORY_FILE):
    pd.DataFrame(columns=["username", "timestamp", "selected_mood", "selected_occasion", "selected_notes", "recommended_perfumes"]).to_csv(HISTORY_FILE, index=False)

# ---------------- App Config ----------------
st.set_page_config(page_title="Perfume Matchmaker", layout="centered")

# ---------------- Load Perfume Data ----------------
df = pd.read_csv(DATA_FILE, encoding="ISO-8859-1")
df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")

# ---------------- Helper Functions ----------------
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def load_users():
    return pd.read_csv(USER_FILE)

def save_user(username, password_hash):
    df = pd.read_csv(USER_FILE)
    df.loc[len(df)] = [username, password_hash]
    df.to_csv(USER_FILE, index=False)

def log_history(username, mood, occasion, notes, recommendations):
    df = pd.read_csv(HISTORY_FILE)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    recommended_perfumes = " | ".join(recommendations)
    df.loc[len(df)] = [username, timestamp, mood, occasion, str(notes), recommended_perfumes]
    df.to_csv(HISTORY_FILE, index=False)

def get_user_history(username):
    df = pd.read_csv(HISTORY_FILE)
    return df[df["username"] == username]

# ---------------- Session Init ----------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# ---------------- Login/Register ----------------
def login_page():
    st.title("🔐 Login or Register")

    menu = st.radio("Choose an option:", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if menu == "Login":
        if st.button("Login"):
            users = load_users()
            user_row = users[users["username"] == username]
            if not user_row.empty and check_password(password, user_row.iloc[0]["password_hash"]):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")
    else:
        if st.button("Register"):
            users = load_users()
            if username in users["username"].values:
                st.warning("Username already exists.")
            else:
                hashed = hash_password(password)
                save_user(username, hashed)
                st.success("Registered! You can now log in.")

# ---------------- App Main Logic ----------------
def main_app():
    st.title("🌸 Perfume Personality Matchmaker")
    st.markdown("Let your vibes choose your scent. Answer a few questions and we'll match you with your signature fragrance!")

    # Step 1 – Mood
    if st.session_state.step == 1:
        st.subheader("Step 1: What's your current vibe?")
        mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
        if st.button("Next ➡️"):
            st.session_state.answers["mood"] = mood
            st.session_state.step += 1
            st.experimental_rerun()

    # Step 2 – Occasion
    elif st.session_state.step == 2:
        st.subheader("Step 2: What's the occasion?")
        occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])
        if st.button("Next ➡️"):
            st.session_state.answers["occasion"] = occasion
            st.session_state.step += 1
            st.experimental_rerun()

    # Step 3 – Notes
    elif st.session_state.step == 3:
        st.subheader("Step 3: What kind of notes do you love?")
        notes = st.multiselect("Pick a few that speak to your soul 💫", 
                               ["Vanilla", "Oud", "Citrus", "Floral", "Spicy", "Woody", "Sweet", "Musky"])
        if st.button("Get My Recommendations 💖"):
            st.session_state.answers["notes"] = notes
            st.session_state.step += 1
            st.experimental_rerun()

    # Step 4 – Results
    elif st.session_state.step == 4:
        st.subheader("💐 Based on your vibe, you might love these:")

        mood = st.session_state.answers["mood"]
        occasion = st.session_state.answers["occasion"]
        notes = st.session_state.answers["notes"]

        query_keywords = [mood, occasion] + notes
        query_string = "|".join(query_keywords)

        results = df[df["combined"].str.contains(query_string, case=False, na=False)]

        recommended_names = []

        if not results.empty:
            for _, row in results.head(5).iterrows():
                st.markdown(f"### **{row['Name']}** by *{row['Brand']}*")
                if pd.notna(row["Image URL"]):
                    st.image(row["Image URL"], width=180)
                st.write(row["Description"])
                st.markdown("---")
                recommended_names.append(row["Name"])
        else:
            st.error("No perfect match found 😢 Try a different mood or notes!")

        log_history(st.session_state.username, mood, occasion, notes, recommended_names)

        if st.button("🔄 Start Over"):
            st.session_state.step = 1
            st.session_state.answers = {}
            st.experimental_rerun()

    if st.button("📜 View My History"):
        history = get_user_history(st.session_state.username)
        if history.empty:
            st.info("No history yet.")
        else:
            st.subheader("Your Past Recommendations:")
            st.dataframe(history)

    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.step = 1
        st.session_state.answers = {}
        st.experimental_rerun()

# ---------------- Run App ----------------
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
