import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import json
import os
import nltk
from nltk.corpus import stopwords

# --- NLTK Data Download ---
@st.cache_data
def download_nltk_data():
    """
    Downloads required NLTK data resources.
    This function is cached to prevent re-downloading on every rerun.
    """
    try:
        nltk.download('stopwords')
        nltk.download('punkt')
        return True
    except Exception as e:
        st.error(f"Failed to download NLTK data: {e}")
        return False

# Call the download function once at the start
if not download_nltk_data():
    st.stop() # Stop the app if download fails

# Get the set of English stopwords from NLTK
stop_words = set(stopwords.words('english'))

# --- Constants and Configuration ---
DATA_FILE = "feedback_data.json"
TOPIC_FILE = "topic_data.json"  # New file for the shared topic
APP_TITLE = "Dynamic Feedback & Word Cloud Dashboard"

# --- Data Handling Functions ---

def load_data():
    """Load feedback data from a JSON file. Create a new file if it doesn't exist."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    """Save feedback data to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_topic():
    """Load the current topic from a shared JSON file."""
    if os.path.exists(TOPIC_FILE):
        with open(TOPIC_FILE, "r") as f:
            topic_data = json.load(f)
            return topic_data.get("current_topic", "")
    return ""

def save_topic(topic):
    """Save the current topic to the shared JSON file."""
    with open(TOPIC_FILE, "w") as f:
        json.dump({"current_topic": topic}, f)

# --- App State Initialization ---

if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = load_data()

if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# --- UI Layout and Components ---

st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)
st.markdown("---")

# Load the topic from the shared file at the start of every run
current_topic = load_topic()

# Left Column for Feedback Input
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Submit Your Feedback")
    # Display the current topic to the users
    if current_topic:
        st.markdown(f"**Topic for Feedback:** `{current_topic}`")
    else:
        st.info("The administrator has not set a topic yet.")
    
    with st.form("feedback_form", clear_on_submit=True):
        feedback = st.text_area("Your Feedback", placeholder="Enter your opinion or comments here...")
        submitted = st.form_submit_button("Submit Feedback")

    if submitted:
        if current_topic and feedback:
            new_entry = {"topic": current_topic, "feedback": feedback}
            st.session_state.feedback_data.append(new_entry)
            save_data(st.session_state.feedback_data)
            st.success("Thank you for your feedback!")
        else:
            st.error("Please ensure a topic is set and provide feedback.")

# Right Column for Word Cloud
with col2:
    st.header("Live Word Cloud")
    if not st.session_state.feedback_data:
        st.info("No feedback yet. Submit some to see the word cloud!")
    else:
        # Combine all feedback into a single string
        all_feedback_text = " ".join([entry['feedback'] for entry in st.session_state.feedback_data])

        # Generate the word cloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='viridis',
            max_words=100,
            stopwords=stop_words).generate(all_feedback_text)

        # Display the word cloud using Matplotlib
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)

st.markdown("---")

# Admin Section
st.header("Admin Access")
try:
    admin_password_secret = st.secrets["admin_password"]
except KeyError:
    st.info("Please set up your admin password in a `.streamlit/secrets.toml` file.")
    admin_password_secret = None

if not st.session_state.admin_logged_in:
    password = st.text_input("Enter Admin Password", type="password")
    if st.button("Log In"):
        if password == admin_password_secret:
            st.session_state.admin_logged_in = True
            st.success("Admin access granted!")
            st.rerun()
        else:
            st.error("Invalid password.")
else:
    st.success("You are logged in as Admin.")
    
    # Manage topic and clear word cloud
    st.subheader("Manage Dashboard")
    col_topic_clear, col_topic_set = st.columns([1,1])

    with col_topic_set:
        new_topic = st.text_input("Set a new topic for feedback", value=current_topic, label_visibility="collapsed")
        if st.button("Set Topic", use_container_width=True):
            save_topic(new_topic)
            st.success(f"Topic set to: '{new_topic}'")
            st.rerun()
    
    with col_topic_clear:
        if st.button("Clear Topic", use_container_width=True):
            save_topic("")
            st.warning("Topic has been cleared.")
            st.rerun()
        if st.button("Clear Word Cloud", use_container_width=True):
            st.session_state.feedback_data = []
            save_data(st.session_state.feedback_data)
            st.warning("All collected feedback has been cleared.")
            st.rerun()

    st.markdown("---")
    st.subheader("Download Data")
    
    # Download button for admin
    download_data = json.dumps(st.session_state.feedback_data, indent=4)
    st.download_button(
        label="Download All Feedback Data (JSON)",
        data=download_data,
        file_name="feedback_data.json",
        mime="application/json",
        help="Download the full dataset of collected feedback."
    )
