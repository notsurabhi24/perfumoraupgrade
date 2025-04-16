import streamlit as st
import pandas as pd
import hashlib
import sqlite3
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Load perfume data
@st.cache_data
def load_data():
    df = pd.read_csv("final_perfume_data.csv")
    df = df.dropna(subset=['Description'])
    return df

df = load_data()

# DB functions
def create_connection():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    return conn

def create_usertable():
    conn = create_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')
    conn.execute('''CREATE TABLE IF NOT EXISTS history(username TEXT, perfume TEXT)''')
    conn.commit()
    conn.close()

def add_userdata(username, password):
    conn = create_connection()
    conn.execute('INSERT INTO userstable(username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM userstable WHERE username=? AND password=?', (username, password))
    data = cur.fetchone()
    conn.close()
    return data

def save_history(username, perfume):
    conn = create_connection()
    conn.execute("INSERT INTO history(username, perfume) VALUES (?, ?)", (username, perfume))
    conn.commit()
    conn.close()

def view_history(username):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT perfume FROM history WHERE username=?", (username,))
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# AI recommendation
@st.cache_data
def recommend_perfumes(user_input):
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['Description'])
    user_vec = tfidf.transform([user_input])
    similarity = cosine_similarity(user_vec, tfidf_matrix).flatten()
    top_indices = similarity.argsort()[-5:][::-1]
    return df.iloc[top_indices]

# UI pages
def show_login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        hashed_pw = hash_password(password)
        user = login_user(username, hashed_pw)
        if user:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
        else:
            st.error("Invalid credentials")
    if st.button("Register"):
        st.session_state["register"] = True

def show_register():
    st.title("Register")
    username = st.text_input("New Username")
    password = st.text_input("New Password", type='password')
    if st.button("Create Account"):
        hashed_pw = hash_password(password)
        add_userdata(username, hashed_pw)
        st.success("Account created! Please login.")
        st.session_state["register"] = False

def show_questionnaire():
    st.title("Perfume Preference Questionnaire")
    q1 = st.selectbox("What mood do you want the perfume to evoke?", ["Romantic", "Fresh", "Bold", "Calm"])
    q2 = st.selectbox("Preferred scent family?", ["Floral", "Woody", "Oriental", "Citrus"])
    q3 = st.selectbox("When do you plan to wear it?", ["Day", "Night", "Special Occasions"])
    if st.button("Get Recommendations"):
        user_input = f"{q1} {q2} {q3}"
        results = recommend_perfumes(user_input)
        st.subheader("Top Perfume Matches:")
        for _, row in results.iterrows():
            st.write(f"**{row['Perfume Name']}** - {row['Description']}")
            save_history(st.session_state["username"], row['Perfume Name'])

def show_history():
    st.title("Your Recommendation History")
    history = view_history(st.session_state["username"])
    if history:
        for item in history:
            st.write("-", item)
    else:
        st.info("No history yet. Try out the questionnaire!")

def main():
    st.set_page_config(page_title="Perfume Recommender", layout="wide")
    create_usertable()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "register" not in st.session_state:
        st.session_state.register = False

    if st.session_state.register:
        show_register()
    elif not st.session_state.logged_in:
        show_login()
    else:
        st.sidebar.title("Navigation")
        choice = st.sidebar.radio("Go to", ["Questionnaire", "History"])

        if choice == "Questionnaire":
            show_questionnaire()
        elif choice == "History":
            show_history()

if __name__ == '__main__':
    main()
