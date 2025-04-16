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
        st.session_state.step = 2  # Move to next step directly
        st.session_state.answers["mood"] = mood  # Store the mood
        # No rerun required, move directly to next step in flow

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

# Step 4 – Results (NLP model)
elif st.session_state.step == 4:
    st.subheader("💐 Based on your vibe, you might love these:")

    mood = st.session_state.answers["mood"]
    occasion = st.session_state.answers["occasion"]
    notes = st.session_state.answers["notes"]

    # NLP Model: Using TF-IDF and Cosine Similarity to match the user's preferences with perfumes
    query_keywords = [mood, occasion] + notes
    query_string = " ".join(query_keywords)  # Combining all user preferences into a single query string

    # Initialize TF-IDF vectorizer and fit on the combined text (Description + Notes)
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(df['combined'])

    # Convert query string to TF-IDF vector
    query_tfidf = vectorizer.transform([query_string])

    # Compute cosine similarity between query and perfume dataset
    cosine_sim = cosine_similarity(query_tfidf, tfidf_matrix)

    # Get top 5 most similar perfumes based on the cosine similarity
    top_matches = cosine_sim[0].argsort()[-5:][::-1]  # Get indices of top 5 matches

    if len(top_matches) > 0:
        for idx in top_matches:
            row = df.iloc[idx]
            st.markdown(f"### *{row['Name']}* by {row['Brand']}")
            if pd.notna(row["Image URL"]):
                st.image(row["Image URL"], width=180)
            st.write(row["Description"])
            st.markdown("---")
    else:
        st.error("No perfect match found 😢 Try a different mood or notes!")

    if st.button("🔄 Start Over"):
        st.session_state.step = 1
        st.session_state.answers = {}
        # Resetting and no rerun needed since step will be reset manually
