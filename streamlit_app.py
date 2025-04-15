import streamlit as st
import pandas as pd
import bcrypt

# Try to load the existing CSV files or create empty ones
try:
    users_df = pd.read_csv("users.csv")
except FileNotFoundError:
    users_df = pd.DataFrame(columns=["username", "password", "email"])

try:
    history_df = pd.read_csv("history.csv")
except FileNotFoundError:
    history_df = pd.DataFrame(columns=["username", "history"])

# Hash password function
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Check password function
def check_password(stored_password, input_password):
    return bcrypt.checkpw(input_password.encode('utf-8'), stored_password.encode('utf-8'))

# Register the user
def register_user(username, password, email):
    if username in users_df['username'].values:
        return False  # User already exists
    hashed_pw = hash_password(password)
    new_user = pd.DataFrame({"username": [username], "password": [hashed_pw], "email": [email]})
    global users_df
    users_df = pd.concat([users_df, new_user], ignore_index=True)
    users_df.to_csv("users.csv", index=False)
    # Create initial history entry for the user
    history_data = pd.DataFrame({"username": [username], "history": ['']})
    global history_df
    history_df = pd.concat([history_df, history_data], ignore_index=True)
    history_df.to_csv("history.csv", index=False)
    return True

# Save user history and recommendations
def save_user_history(username, answers, recommended_perfumes):
    global history_df
    history_entry = {
        "username": username,
        "history": f"Answers: {answers}, Recommended: {recommended_perfumes}"
    }
    history_df = history_df.append(history_entry, ignore_index=True)
    history_df.to_csv("history.csv", index=False)

# Session state init
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# Function for login/register screen
def login_or_register():
    if not st.session_state.user_logged_in:
        choice = st.radio("Do you have an account?", ["Login", "Register"])
        
        if choice == "Login":
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                if username in users_df['username'].values:
                    stored_password = users_df[users_df["username"] == username].iloc[0]['password']
                    if check_password(stored_password, password):
                        st.session_state.user_logged_in = True
                        st.session_state.username = username
                        st.success(f"Logged in as {username}")
                    else:
                        st.error("Incorrect password!")
                else:
                    st.error("Username not found!")
        
        elif choice == "Register":
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
                        st.success(f"Registered and logged in as {username}")
                    else:
                        st.error("Username already exists!")
                else:
                    st.error("Passwords do not match!")

    else:
        st.write(f"Logged in as {st.session_state.username}")
        st.button("Logout", on_click=logout)

# Logout function
def logout():
    st.session_state.user_logged_in = False
    st.session_state.username = ""
    st.session_state.answers = {}
    st.session_state.step = 1

# Function for perfume recommendations
def perfume_recommender():
    if st.session_state.user_logged_in:
        if st.session_state.step == 1:
            st.subheader("What's your current vibe?")
            mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
            if st.button("Next ➡️"):
                st.session_state.answers["mood"] = mood
                st.session_state.step += 1

        elif st.session_state.step == 2:
            st.subheader("What's the occasion?")
            occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])
            if st.button("Next ➡️"):
                st.session_state.answers["occasion"] = occasion
                st.session_state.step += 1

        elif st.session_state.step == 3:
            st.subheader("What kind of notes do you love?")
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
            
            # Here, you'll filter your perfume data based on the query (assuming you have a `final_perfume_data.csv`)
            df = pd.read_csv("final_perfume_data.csv")
            results = df[df["Description"].str.contains(query_string, case=False, na=False)]

            if not results.empty:
                recommended_perfumes = []
                for _, row in results.head(5).iterrows():
                    recommended_perfumes.append(f"**{row['Name']}** by *{row['Brand']}*")
                    if pd.notna(row["Image URL"]):
                        st.image(row["Image URL"], width=180)
                    st.write(row["Description"])
                    st.markdown("---")

                save_user_history(st.session_state.username, st.session_state.answers, recommended_perfumes)
            else:
                st.error("No perfect match found 😢 Try a different mood or notes!")

            if st.button("🔄 Start Over"):
                st.session_state.step = 1
                st.session_state.answers = {}

    else:
        login_or_register()

# Run the app
perfume_recommender()
