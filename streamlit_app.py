import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, auth
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize Firebase Admin SDK
cred = credentials.Certificate("path_to_your_service_account_key.json")
firebase_admin.initialize_app(cred)

# Load dataset
df = pd.read_csv("final_perfume_data.csv", encoding="ISO-8859-1")

# Combine text for searching using the correct column names
df["combined"] = df["Description"].fillna("") + " " + df["Notes"].fillna("")

# Session state init
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Function to register user
def register_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        return user.uid
    except Exception as e:
        return f"Error: {str(e)}"

# Function to log in user
def login_user(email, password):
    try:
        user = auth.get_user_by_email(email)
        # Password verification is done by Firebase
        return user.uid
    except Exception as e:
        return f"Error: {str(e)}"

# NLP-based recommendation function
def recommend_perfumes(mood, occasion, notes):
    # Use TF-IDF Vectorizer to match keywords with perfume descriptions
    query_keywords = [mood, occasion] + notes
    query_string = " ".join(query_keywords)
    
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df["combined"].values)
    query_tfidf = tfidf.transform([query_string])
    
    # Compute cosine similarity between the query and perfume descriptions
    cosine_similarities = cosine_similarity(query_tfidf, tfidf_matrix)
    similar_indices = cosine_similarities.argsort()[0][-5:][::-1]  # Top 5 matches
    
    # Show top matches
    recommendations = []
    for idx in similar_indices:
        recommendations.append(df.iloc[idx])
    
    return recommendations

# Questionnaire and Recommendations flow
def show_questionnaire():
    if st.session_state.step == 1:
        st.subheader("Step 1: What's your current vibe?")
        mood = st.radio("", ["Romantic", "Bold", "Fresh", "Mysterious", "Cozy", "Energetic"])
        if st.button("Next ➡"):
            st.session_state.answers["mood"] = mood
            st.session_state.step = 2  # Move to next step

    elif st.session_state.step == 2:
        st.subheader("Step 2: What's the occasion?")
        occasion = st.radio("", ["Everyday Wear", "Date Night", "Work", "Party"])
        if st.button("Next ➡"):
            st.session_state.answers["occasion"] = occasion
            st.session_state.step = 3  # Move to next step

    elif st.session_state.step == 3:
        st.subheader("Step 3: What kind of notes do you love?")
        notes = st.multiselect("Pick a few that speak to your soul 💫", 
                               ["Vanilla", "Oud", "Citrus", "Floral", "Spicy", "Woody", "Sweet", "Musky"])
        if st.button("Get My Recommendations 💖"):
            st.session_state.answers["notes"] = notes
            st.session_state.step = 4  # Proceed to results

    elif st.session_state.step == 4:
        st.subheader("💐 Based on your vibe, you might love these:")
        
        mood = st.session_state.answers["mood"]
        occasion = st.session_state.answers["occasion"]
        notes = st.session_state.answers["notes"]
        
        # Get recommendations based on NLP
        recommendations = recommend_perfumes(mood, occasion, notes)
        
        for perfume in recommendations:
            st.markdown(f"### *{perfume['Name']}* by {perfume['Brand']}")
            if pd.notna(perfume["Image URL"]):
                st.image(perfume["Image URL"], width=180)
            st.write(perfume["Description"])
            st.markdown("---")
        
        if st.button("🔄 Start Over"):
            st.session_state.step = 1
            st.session_state.answers = {}

# User login function
def user_login():
    st.title("Login or Register")
    
    option = st.radio("Select", ["Login", "Register"])
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if option == "Register":
        if st.button("Register"):
            result = register_user(email, password)
            st.write(f"User Registered! {result}")
            
    elif option == "Login":
        if st.button("Login"):
            result = login_user(email, password)
            st.write(f"Login successful! {result}")
            st.session_state.logged_in = True

if __name__ == "__main__":
    if not st.session_state.logged_in:
        user_login()
    else:
        show_questionnaire()
