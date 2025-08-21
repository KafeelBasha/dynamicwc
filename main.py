import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
import json
from collections import defaultdict

try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

try:
    if not firebase_admin._apps:
        cred_dict = st.secrets["firebase"]
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': cred_dict["databaseURL"]
        })
except Exception as e:
    st.error(f"Error initializing Firebase: {e}")
    st.info("Please ensure your Firebase Admin SDK credentials are set up correctly in `secrets.toml`.")
    st.stop()


active_topic_ref = db.reference("active_topic")
feedback_ref = db.reference("all_feedback")


st.set_page_config(layout="wide", page_title="Live Feedback Word Cloud")
st.title("Live Feedback & Word Cloud Dashboard")
st.markdown("---")

st.header("Admin: Manage Topics")
current_topic = active_topic_ref.get() or ""
st.write(f"**Current Active Topic:** `{current_topic}`")

new_topic = st.text_input("Set a New Topic", value=current_topic)
if st.button("Set as Active Topic"):
    if new_topic.strip():
        active_topic_ref.set(new_topic.strip())
        st.success(f"Topic '{new_topic.strip()}' is now active!")
        st.experimental_rerun()
    else:
        st.error("Topic cannot be empty.")

st.markdown("---")

st.header("Submit Your Feedback")
current_topic_for_user = active_topic_ref.get()
if current_topic_for_user:
    st.write(f"Please provide your feedback on the topic: **{current_topic_for_user}**")
    feedback = st.text_area("Your Feedback", placeholder="Enter your thoughts...", key="user_feedback")
    if st.button("Submit Feedback"):
        if feedback.strip():
            feedback_ref.push({
                "topic": current_topic_for_user,
                "feedback": feedback.strip()
            })
            st.success("Feedback submitted!")
            st.experimental_rerun()
        else:
            st.error("Feedback cannot be empty.")
else:
    st.info("An admin needs to set an active topic before you can submit feedback.")

st.markdown("---")

st.header("Word Clouds by Topic")
all_feedback = feedback_ref.get()

if all_feedback:
    feedback_by_topic = defaultdict(list)
    
    for entry in all_feedback.values():
        if "topic" in entry and "feedback" in entry:
            feedback_by_topic[entry["topic"]].append(entry["feedback"])

    for topic, feedback_list in feedback_by_topic.items():
        st.subheader(f"Word Cloud for Topic: '{topic}'")
        combined_text = " ".join(feedback_list)
        
        if combined_text.strip():
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
            st.info(f"No feedback available for this topic yet.")
else:
    st.info("No feedback has been submitted yet.")

st.markdown("---")

st.header("Admin: Tools")

col1, col2 = st.columns(2)

with col1:
    if st.button("Clear All Feedback"):
        feedback_ref.delete()
        st.warning("All feedback cleared.")
        st.experimental_rerun()

with col2:
    if st.button("Download All Feedback Data"):
        if all_feedback:
            json_data = json.dumps(all_feedback, indent=4)
            st.download_button(
                label="Download Feedback JSON",
                data=json_data,
                file_name="all_feedback_data.json",
                mime="application/json"
            )
        else:
            st.info("No feedback to download.")
