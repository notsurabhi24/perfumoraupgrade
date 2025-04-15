import streamlit as st
import pandas as pd
import sqlite3
import re

# Load dataset for perfumes
df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")
df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")

# Initialize the SQLite database
def create_connection():
    conn = sqlite3.connect('perfume_app.db')
    return conn

# Create table for users if not exists
def create_users_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Create table for storing perfume recommendations history
def create_history_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                      user_id INTEGER,
                      perfume_name TEXT,
                      perfume_brand TEXT,
                      recommendation_date TEXT,
                      FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

# Function to register a new user
def register_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# Function to login an existing user
def login_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Function to save perfume history
def save_history(user_id, perfume_name, perfume_brand):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (user_id, perfume_name, perfume_brand, recommendation_date) VALUES (?, ?, ?, ?)",
                   (user_id, perfume_name, perfume_brand, pd.to_datetime("today").strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

# Highlight matching keywords in perfume description
def highlight_matching_words(text, keywords):
    for keyword in keywords:
        text = re.sub(f'({keyword})', r'<span style="color:red">\1</span>', text, flags=re.IGNORECASE)
    return text

# Function to display the questionnaire and recommendations
def show_questionnaire():
    # Step 1 – Mood
    st.subheader("Step 1: What's your current vibe?")
    mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])

    # Step 2 – Occasion
    st.subheader("Step 2: What's the occasion?")
    occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])

    # Step 3 – Notes
    st.subheader("Step 3: What kind of notes do you love?")
    notes = st.multiselect("Pick a few that speak to your soul 💫", 
                           ["Vanilla", "Oud", "Citrus", "Floral", "Spicy", "Woody", "Sweet", "Musky"])

    # Step 4 – Results
    if st.button("Get My Recommendations 💖"):
        query_keywords = [mood, occasion] + notes
        query_string = "|".join(query_keywords)

        # Search for matches in the combined text
        results = df[df["combined"].str.contains(query_string, case=False, na=False)]

        if not results.empty:
            for _, row in results.head(5).iterrows():
                highlighted_description = highlight_matching_words(row["Description"], query_keywords)
                st.markdown(f"### *{row['Name']}* by {row['Brand']}")
                if pd.notna(row["Image URL"]):
                    st.image(row["Image URL"], width=180)
                st.markdown(f"<div>{highlighted_description}</div>", unsafe_allow_html=True)
                st.markdown("---")
                save_history(st.session_state.user_id, row["Name"], row["Brand"])
        else:
            st.error("No perfect match found 😢 Try a different mood or notes!")

# Login/Register Flow
def login_register_page():
    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Select Activity", menu)

    # Registration Page
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

    # Login Page
    elif choice == "Login":
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user_id = user[0]  # Store user ID in session state
                st.session_state.username = username
                st.success(f"Welcome {username}")
                show_questionnaire()
            else:
                st.warning("Invalid username or password.")

# Main Function
def main():
    create_users_table()
    create_history_table()
    login_register_page()

if __name__ == "__main__":
    main()
