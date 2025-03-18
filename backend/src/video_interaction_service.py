# video_interaction_service.py
import cv2
import numpy as np
import json
import logging
import os
from datetime import datetime
import uuid
import face_recognition
from database_connector import DatabaseConnector

class VideoInteractionService:
    def __init__(self, db_connector=None):
        self.db_connector = db_connector or DatabaseConnector()
        self.logger = logging.getLogger(__name__)
        self.sessions = {}  # Store active sessions

    def start_session(self, user_id):
        """
        Start a new video interaction session
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: Session information
        """
        try:
            session_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": timestamp,
                "status": "active",
                "face_encodings": [],
                "conversation_stage": "introduction"
            }
            
            # Store session in memory
            self.sessions[session_id] = session_data
            
            # Store session in database
            self.db_connector.insert_session(session_data)
            
            return {
                "status": "success",
                "session_id": session_id,
                "message": "Session started successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error starting session: {str(e)}")
            return {
                "status": "error",
                "message": f"Error starting session: {str(e)}"
            }
    
    def end_session(self, session_id):
        """
        End a video interaction session
        
        Args:
            session_id: ID of the session
            
        Returns:
            dict: Result of ending the session
        """
        try:
            if session_id not in self.sessions:
                return {
                    "status": "error",
                    "message": "Session not found"
                }
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update session data
            self.sessions[session_id]["status"] = "completed"
            self.sessions[session_id]["end_time"] = timestamp
            
            # Update database
            self.db_connector.update_session(self.sessions[session_id])
            
            # Remove from memory
            del self.sessions[session_id]
            
            return {
                "status": "success",
                "message": "Session ended successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error ending session: {str(e)}")
            return {
                "status": "error",
                "message": f"Error ending session: {str(e)}"
            }
    
    def process_user_frame(self, session_id, frame):
        """
        Process a video frame from the user
        
        Args:
            session_id: ID of the session
            frame: numpy array of the video frame
            
        Returns:
            dict: Processing result including face verification
        """
        try:
            if session_id not in self.sessions:
                return {
                    "status": "error",
                    "message": "Session not found"
                }
            
            # Detect faces in the frame
            face_locations = face_recognition.face_locations(frame)
            
            if not face_locations:
                return {
                    "status": "no_face",
                    "message": "No face detected in frame"
                }
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            
            # If this is the first frame with a face, store the encoding
            if not self.sessions[session_id]["face_encodings"]:
                self.sessions[session_id]["face_encodings"] = face_encodings[0].tolist()
                
                return {
                    "status": "face_registered",
                    "message": "Face registered successfully"
                }
            
            # Compare with stored face encoding
            matches = face_recognition.compare_faces(
                [np.array(self.sessions[session_id]["face_encodings"])], 
                face_encodings[0]
            )
            
            if not matches[0]:
                return {
                    "status": "different_face",
                    "message": "Different person detected"
                }
            
            # Update session data
            self.sessions[session_id]["last_interaction"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                "status": "success",
                "message": "Face verified successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing user frame: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing frame: {str(e)}"
            }
    
    def save_user_response(self, session_id, response_data):
        """
        Save user video response
        
        Args:
            session_id: ID of the session
            response_data: Dict containing response information
            
        Returns:
            dict: Result of saving the response
        """
        try:
            if session_id not in self.sessions:
                return {
                    "status": "error",
                    "message": "Session not found"
                }
            
            # Generate unique filename
            filename = f"{session_id}_{response_data['question_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
            filepath = f"responses/{filename}"
            
            # Save video to disk
            with open(filepath, 'wb') as f:
                f.write(response_data['video_data'])
            
            # Save response metadata to database
            response_metadata = {
                "session_id": session_id,
                "question_id": response_data['question_id'],
                "response_path": filepath,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration": response_data.get('duration', 0),
                "transcription": response_data.get('transcription', "")
            }
            
            self.db_connector.insert_response(response_metadata)
            
            # Update session conversation stage
            self.sessions[session_id]["conversation_stage"] = response_data.get("next_stage", self.sessions[session_id]["conversation_stage"])
            self.db_connector.update_session(self.sessions[session_id])
            
            return {
                "status": "success",
                "message": "Response saved successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error saving user response: {str(e)}")
            return {
                "status": "error",
                "message": f"Error saving response: {str(e)}"
            }
    
    def get_next_interaction(self, session_id):
        """
        Get the next interaction for the user based on the current conversation stage
        
        Args:
            session_id: ID of the session
            
        Returns:
            dict: Next interaction details
        """
        try:
            if session_id not in self.sessions:
                return {
                    "status": "error",
                    "message": "Session not found"
                }
            
            stage = self.sessions[session_id]["conversation_stage"]
            
            # Get next interaction from database based on current stage
            next_interaction = self.db_connector.get_next_interaction(stage)
            
            if not next_interaction:
                return {
                    "status": "error",
                    "message": "No next interaction found"
                }
            
            return {
                "status": "success",
                "interaction": next_interaction
            }
            
        except Exception as e:
            self.logger.error(f"Error getting next interaction: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting next interaction: {str(e)}"
            }