import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords

# --- NLTK Setup ---
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# --- Firebase Setup ---
# Replace with your Firebase Admin SDK JSON path
cred = credentials.Certificate("firebase_admin_sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-project-id.firebaseio.com/'
})

# --- Firebase References ---
topic_ref = db.reference("topic")
feedback_ref = db.reference("feedback")

# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="Live Feedback Word Cloud")
st.title("Live Feedback & Word Cloud Dashboard")
st.markdown("---")

# --- Topic Display & Update ---
current_topic = topic_ref.get() or ""
st.subheader("Current Topic")
st.write(f"**Topic:** `{current_topic}`")

new_topic = st.text_input("Set New Topic", value=current_topic)
if st.button("Update Topic"):
    topic_ref.set(new_topic)
    st.success("Topic updated!")
    st.experimental_rerun()

# --- Feedback Submission ---
st.subheader("Submit Feedback")
feedback = st.text_area("Your Feedback", placeholder="Enter your thoughts...")
if st.button("Submit Feedback"):
    if current_topic and feedback.strip():
        feedback_ref.push({"topic": current_topic, "feedback": feedback.strip()})
        st.success("Feedback submitted!")
        st.experimental_rerun()
    else:
        st.error("Please enter feedback and ensure a topic is set.")

# --- Word Cloud Display ---
st.subheader("Live Word Cloud")
all_feedback = feedback_ref.get()
if all_feedback:
    combined_text = " ".join([entry["feedback"] for entry in all_feedback.values()])
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        colormap='viridis',
        max_words=100,
        stopwords=stop_words
    ).generate(combined_text)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)
else:
    st.info("No feedback yet. Submit some to see the word cloud!")

# --- Admin Tools ---
st.markdown("---")
st.subheader("Admin Tools")

if st.button("Clear Topic"):
    topic_ref.set("")
    st.warning("Topic cleared.")
    st.experimental_rerun()

if st.button("Clear All Feedback"):
    feedback_ref.delete()
    st.warning("All feedback cleared.")
    st.experimental_rerun()

if st.button("Download Feedback Data"):
    import json
    feedback_data = feedback_ref.get()
    if feedback_data:
        json_data = json.dumps(feedback_data, indent=4)
        st.download_button(
            label="Download Feedback JSON",
            data=json_data,
            file_name="feedback_data.json",
            mime="application/json"
        )
    else:
        st.info("No feedback to download.")
