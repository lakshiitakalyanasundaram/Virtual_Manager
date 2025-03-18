import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime
import logging
import uuid

class FaceVerificationSystem:
    def __init__(self, user_profile_directory="user_profiles", verification_threshold=0.6):
        """
        Initialize the face verification system.
        
        Args:
            user_profile_directory: Directory where user profile images are stored
            verification_threshold: Threshold for face matching (lower is stricter)
        """
        self.user_profile_directory = user_profile_directory
        self.verification_threshold = verification_threshold
        self.logger = logging.getLogger(__name__)
        
        # Ensure the profile directory exists
        if not os.path.exists(self.user_profile_directory):
            os.makedirs(self.user_profile_directory)
            self.logger.info(f"Created directory: {self.user_profile_directory}")
    
    def register_user(self, user_id, profile_image):
        """
        Register a new user with their profile image.
        
        Args:
            user_id: Unique identifier for the user
            profile_image: User's profile image (numpy array)
            
        Returns:
            dict: Registration result
        """
        try:
            # Detect face in the profile image
            face_locations = face_recognition.face_locations(profile_image)
            
            if not face_locations:
                return {
                    "status": "error",
                    "message": "No face detected in profile image"
                }
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(profile_image, face_locations)
            
            if not face_encodings:
                return {
                    "status": "error",
                    "message": "Failed to encode face"
                }
            
            # Create user directory if it doesn't exist
            user_dir = os.path.join(self.user_profile_directory, str(user_id))
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            
            # Save profile image
            profile_path = os.path.join(user_dir, "profile.jpg")
            cv2.imwrite(profile_path, profile_image)
            
            # Save face encoding
            encoding_path = os.path.join(user_dir, "face_encoding.npy")
            np.save(encoding_path, face_encodings[0])
            
            return {
                "status": "success",
                "message": "User registered successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error registering user: {str(e)}")
            return {
                "status": "error",
                "message": f"Error registering user: {str(e)}"
            }
    
    def verify_face(self, user_id, frame):
        """
        Verify a face in a video frame against the user's profile.
        
        Args:
            user_id: ID of the user to verify
            frame: Video frame containing the face to verify
            
        Returns:
            dict: Verification result
        """
        try:
            # Check if user exists
            user_dir = os.path.join(self.user_profile_directory, str(user_id))
            encoding_path = os.path.join(user_dir, "face_encoding.npy")
            
            if not os.path.exists(encoding_path):
                return {
                    "status": "error",
                    "message": "User not registered"
                }
            
            # Load stored face encoding
            stored_encoding = np.load(encoding_path)
            
            # Detect face in the frame
            face_locations = face_recognition.face_locations(frame)
            
            if not face_locations:
                return {
                    "status": "no_face",
                    "message": "No face detected in frame"
                }
            
            # Get face encoding from frame
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            
            if not face_encodings:
                return {
                    "status": "error",
                    "message": "Failed to encode face in frame"
                }
            
            # Compare face encodings
            face_distances = face_recognition.face_distance([stored_encoding], face_encodings[0])
            
            if face_distances[0] <= self.verification_threshold:
                return {
                    "status": "success",
                    "message": "Face verified successfully",
                    "confidence": float(1 - face_distances[0]),
                    "face_location": face_locations[0]
                }
            else:
                return {
                    "status": "different_face",
                    "message": "Face does not match the registered user",
                    "confidence": float(1 - face_distances[0])
                }
            
        except Exception as e:
            self.logger.error(f"Error verifying face: {str(e)}")
            return {
                "status": "error",
                "message": f"Error verifying face: {str(e)}"
            }
    
    def track_face_continuity(self, session_id, frame, session_data=None):
        """
        Track face continuity across a session to ensure the same user is present.
        
        Args:
            session_id: ID of the session
            frame: Video frame to process
            session_data: Dictionary containing session information including previous face encodings
            
        Returns:
            dict: Face tracking result
        """
        try:
            # Detect face in the frame
            face_locations = face_recognition.face_locations(frame)
            
            if not face_locations:
                return {
                    "status": "no_face",
                    "message": "No face detected in frame"
                }
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            
            if not face_encodings:
                return {
                    "status": "error",
                    "message": "Failed to encode face in frame"
                }
            
            # If this is the first frame with a face, store the encoding
            if not session_data or "face_encoding" not in session_data:
                return {
                    "status": "face_registered",
                    "message": "Face registered for session",
                    "face_encoding": face_encodings[0].tolist(),
                    "face_location": face_locations[0]
                }
            
            # Compare with stored face encoding from session
            face_distances = face_recognition.face_distance(
                [np.array(session_data["face_encoding"])], 
                face_encodings[0]
            )
            
            if face_distances[0] <= self.verification_threshold:
                return {
                    "status": "same_face",
                    "message": "Same face detected",
                    "confidence": float(1 - face_distances[0]),
                    "face_location": face_locations[0]
                }
            else:
                return {
                    "status": "different_face",
                    "message": "Different person detected",
                    "confidence": float(1 - face_distances[0])
                }
            
        except Exception as e:
            self.logger.error(f"Error tracking face continuity: {str(e)}")
            return {
                "status": "error",
                "message": f"Error tracking face: {str(e)}"
            }
    
    def verify_user_with_profile(self, user_id, frame):
        """
        Verify a user in a video frame against their profile image.
        
        Args:
            user_id: ID of the user
            frame: Video frame containing the face to verify
            
        Returns:
            dict: Verification result
        """
        return self.verify_face(user_id, frame)
    
    def save_verification_result(self, user_id, verification_result, frame=None):
        """
        Save verification result for audit purposes.
        
        Args:
            user_id: ID of the user
            verification_result: Result of the verification
            frame: Video frame (optional)
            
        Returns:
            dict: Save result
        """
        try:
            # Create verification record directory if it doesn't exist
            verification_dir = os.path.join(self.user_profile_directory, str(user_id), "verifications")
            if not os.path.exists(verification_dir):
                os.makedirs(verification_dir)
            
            # Generate unique ID for this verification
            verification_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Save verification result
            result_path = os.path.join(verification_dir, f"{verification_id}_result.json")
            with open(result_path, 'w') as f:
                # Remove numpy arrays from result before saving
                save_result = {k: v for k, v in verification_result.items() 
                               if not isinstance(v, np.ndarray) and k != 'face_location'}
                
                # Add timestamp and verification ID
                save_result['timestamp'] = timestamp
                save_result['verification_id'] = verification_id
                
                # Save as JSON
                import json
                json.dump(save_result, f)
            
            # Save frame if provided
            if frame is not None:
                frame_path = os.path.join(verification_dir, f"{verification_id}_frame.jpg")
                cv2.imwrite(frame_path, frame)
            
            return {
                "status": "success",
                "message": "Verification result saved",
                "verification_id": verification_id
            }
            
        except Exception as e:
            self.logger.error(f"Error saving verification result: {str(e)}")
            return {
                "status": "error",
                "message": f"Error saving verification result: {str(e)}"
            }

class FaceVerificationAPI:
    """
    API interface for the face verification system to integrate with web applications
    """
    def __init__(self, db_connector=None):
        self.face_verification = FaceVerificationSystem()
        self.db_connector = db_connector
        self.logger = logging.getLogger(__name__)
    
    def register_user_profile(self, user_id, profile_image):
        """
        Register a user profile image
        
        Args:
            user_id: User ID
            profile_image: Profile image (numpy array or file path)
            
        Returns:
            dict: Registration result
        """
        try:
            # Load image if path provided
            if isinstance(profile_image, str):
                profile_image = cv2.imread(profile_image)
            
            # Register user
            result = self.face_verification.register_user(user_id, profile_image)
            
            # Update database if successful
            if result["status"] == "success" and self.db_connector:
                self.db_connector.update_user({
                    "user_id": user_id,
                    "face_verification_status": "registered",
                    "face_verification_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            
            return result
        except Exception as e:
            self.logger.error(f"Error registering user profile: {str(e)}")
            return {
                "status": "error",
                "message": f"Error registering user profile: {str(e)}"
            }
    
    def verify_user_in_session(self, session_id, user_id, frame, session_data=None):
        """
        Verify a user in a session, checking both profile and session continuity
        
        Args:
            session_id: Session ID
            user_id: User ID
            frame: Video frame
            session_data: Session data
            
        Returns:
            dict: Verification result
        """
        try:
            # First verify against profile
            profile_result = self.face_verification.verify_user_with_profile(user_id, frame)
            
            # If profile verification failed, return the result
            if profile_result["status"] != "success":
                return profile_result
            
            # Then verify session continuity
            if session_data:
                continuity_result = self.face_verification.track_face_continuity(session_id, frame, session_data)
                
                # If session continuity check failed, return the result
                if continuity_result["status"] not in ["same_face", "face_registered"]:
                    return continuity_result
                
                # Update session data if this is the first face detected
                if continuity_result["status"] == "face_registered" and "face_encoding" in continuity_result:
                    return {
                        "status": "success",
                        "message": "User verified and registered for session",
                        "face_encoding": continuity_result["face_encoding"],
                        "confidence": profile_result.get("confidence", 1.0)
                    }
            
            # Both checks passed
            return {
                "status": "success",
                "message": "User verified successfully",
                "confidence": profile_result.get("confidence", 1.0)
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying user in session: {str(e)}")
            return {
                "status": "error",
                "message": f"Error verifying user: {str(e)}"
            }
    
    def process_video_frame(self, user_id, session_id, frame, session_data=None):
        """
        Process a video frame for face verification
        
        Args:
            user_id: User ID
            session_id: Session ID
            frame: Video frame
            session_data: Session data
            
        Returns:
            dict: Processing result
        """
        try:
            # Verify user
            verification_result = self.verify_user_in_session(session_id, user_id, frame, session_data)
            
            # Save verification result
            self.face_verification.save_verification_result(user_id, verification_result, frame)
            
            return verification_result
            
        except Exception as e:
            self.logger.error(f"Error processing video frame: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing video frame: {str(e)}"
            }