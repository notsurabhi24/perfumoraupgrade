import streamlit as st
import bcrypt
import pandas as pd

# Assuming you have a basic user data storage for login
users = {}

# Function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Function to check if password matches
def check_password(stored_hash, password):
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

# Sample user data (for testing purposes, remove in production)
users["testuser"] = {
    "password": hash_password("testpassword"),  # Hash the password
    "email": "testuser@example.com",
    "history": []  # User's history (will be populated after login)
}

# Login Page function
def login_page():
    st.title("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    
    if st.button("Login"):
        # Check if user exists
        if username in users:
            # Check if the password is correct
            if check_password(users[username]["password"], password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome back, {username}!")
                # Instead of rerunning, you could move to the main page or show the data
                st.experimental_rerun()  # You can keep this, but handle it carefully
            else:
                st.error("Incorrect password. Please try again.")
        else:
            st.error("User not found. Please register.")
    
    if st.session_state.get("logged_in", False):
        st.write(f"Logged in as {st.session_state.username}")
        # Show user history or other relevant data
        st.write("Your history:")
        st.write(users[st.session_state.username]["history"])

# Main app logic
if "logged_in" not in st.session_state:
    login_page()
else:
    # You can display the main content after successful login
    st.write("Main content here")
