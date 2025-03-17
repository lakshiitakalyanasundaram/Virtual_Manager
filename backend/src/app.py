import streamlit as st
import cv2
import tempfile
import os

# Set page layout
st.set_page_config(layout="wide")

# Title
st.title("💬 Virtual AI Branch Manager")

# Layout: Two columns
col1, col2 = st.columns(2)

# Left Side: Play Virtual AI Manager Video
with col1:
    st.header("📹 Virtual AI Manager")
    
    # Load and display the video (stored locally)
    video_path = "/Users/lakshiitakalyanasundaram/Desktop/Machine Learning/Virtual_Manager/ai_videos/intro.mp4"  # Change this to your video path
    if os.path.exists(video_path):
        st.video(video_path)
    else:
        st.error("Virtual Manager video not found!")

# Right Side: Live Video Feed
with col2:
    st.header("🎥 Your Live Video")

    # Open webcam
    cap = cv2.VideoCapture(0)
    
    # Display live video
    stframe = st.empty()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to access camera.")
            break
        
        # Convert frame color (BGR to RGB)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Show the live video feed
        stframe.image(frame, channels="RGB")

    cap.release()
    cv2.destroyAllWindows()
