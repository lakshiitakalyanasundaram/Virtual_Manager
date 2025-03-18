# app.py
from flask import Flask, request, jsonify
import logging
import os
import json
from document_processing_service import DocumentProcessor
from video_interaction_service import VideoInteractionService
from loan_application_service import LoanApplicationService
from database_connector import DatabaseConnector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize services
db_connector = DatabaseConnector()
document_processor = DocumentProcessor(db_connector)
video_service = VideoInteractionService(db_connector)
loan_service = LoanApplicationService(db_connector)

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "message": "AI Branch Manager API is running"
    })

@app.route('/api/users', methods=['POST'])
def create_user():
    """
    Create a new user
    """
    try:
        user_data = request.json
        user_id = db_connector.insert_user(user_data)
        
        return jsonify({
            "status": "success",
            "user_id": user_id,
            "message": "User created successfully"
        })
    except Exception as e:
        logging.error(f"Error creating user: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error creating user"
        }), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get user information
    """
    try:
        user = db_connector.get_user(user_id)
        
        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "user": user
        })
    except Exception as e:
        logging.error(f"Error getting user: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error getting user"
        }), 500

@app.route('/api/sessions', methods=['POST'])
def start_session():
    """
    Start a new video interaction session
    """
    try:
        user_id = request.json.get('user_id')
        
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "User ID is required"
            }), 400
        
        session_result = video_service.start_session(user_id)
        
        return jsonify(session_result)
    except Exception as e:
        logging.error(f"Error starting session: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error starting session"
        }), 500

@app.route('/api/sessions/<session_id>/end', methods=['POST'])
def end_session(session_id):
    """
    End a video interaction session
    """
    try:
        result = video_service.end_session(session_id)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error ending session: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error ending session"
        }), 500

@app.route('/api/sessions/<session_id>/frame', methods=['POST'])
def process_frame(session_id):
    """
    Process a video frame from the user
    """
    try:
        # Extract frame data from request
        frame_data = request.json.get('frame_data')
        
        if not frame_data:
            return jsonify({
                "status": "error",
                "message": "Frame data is required"
            }), 400
        
        # Convert base64 to numpy array
        import numpy as np
        import base64
        import cv2
        
        frame_bytes = base64.b64decode(frame_data)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        
        # Process frame
        result = video_service.process_user_frame(session_id, frame)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error processing frame: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error processing frame"
        }), 500

@app.route('/api/sessions/<session_id>/response', methods=['POST'])
def save_response(session_id):
    """
    Save a user video response
    """
    try:
        response_data = request.json
        
        if not response_data:
            return jsonify({
                "status": "error",
                "message": "Response data is required"
            }), 400
        
        result = video_service.save_user_response(session_id, response_data)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error saving response: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error saving response"
        }), 500

@app.route('/api/sessions/<session_id>/next', methods=['GET'])
def get_next_interaction(session_id):
    """
    Get the next interaction for the user
    """
    try:
        result = video_service.get_next_interaction(session_id)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting next interaction: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error getting next interaction"
        }), 500

@app.route('/api/documents/process', methods=['POST'])
def process_document():
    """
    Process a document from a video frame
    """
    try:
        user_id = request.json.get('user_id')
        frame_data = request.json.get('frame_data')
        
        if not user_id or not frame_data:
            return jsonify({
                "status": "error",
                "message": "User ID and frame data are required"
            }), 400
        
        # Convert base64 to numpy array
        import numpy as np
        import base64
        import cv2
        
        frame_bytes = base64.b64decode(frame_data)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        
        # Process document
        result = document_processor.process_document_frame(user_id, frame)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error processing document: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error processing document"
        }), 500

@app.route('/api/loans', methods=['POST'])
def start_loan_application():
    """
    Start a new loan application
    """
    try:
        user_id = request.json.get('user_id')
        loan_type = request.json.get('loan_type')
        
        if not user_id or not loan_type:
            return jsonify({
                "status": "error",
                "message": "User ID and loan type are required"
            }), 400
        
        result = loan_service.start_application(user_id, loan_type)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error starting loan application: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error starting loan application"
        }), 500

@app.route('/api/loans/<application_id>', methods=['PUT'])
def update_loan_application(application_id):
    """
    Update a loan application
    """
    try:
        update_data = request.json
        
        if not update_data:
            return jsonify({
                "status": "error",
                "message": "Update data is required"
            }), 400
        
        result = loan_service.update_application(application_id, update_data)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error updating loan application: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error updating loan application"
        }), 500

@app.route('/api/loans/<application_id>/eligibility', methods=['GET'])
def check_loan_eligibility(application_id):
    """
    Check loan eligibility
    """
    try:
        result = loan_service.check_eligibility(application_id)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error checking loan eligibility: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error checking loan eligibility"
        }), 500

@app.route('/api/loans/<application_id>/submit', methods=['POST'])
def submit_loan_application(application_id):
    """
    Submit a loan application for processing
    """
    try:
        result = loan_service.submit_application(application_id)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error submitting loan application: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error submitting loan application"
        }), 500

@app.route('/api/loans/<application_id>', methods=['GET'])
def get_loan_application(application_id):
    """
    Get loan application details
    """
    try:
        result = loan_service.get_application(application_id)
        
        if not result:
            return jsonify({
                "status": "error",
                "message": "Loan application not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "application": result
        })
    except Exception as e:
        logging.error(f"Error retrieving loan application: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error retrieving loan application"
        }), 500

@app.route('/api/loans/<application_id>/documents', methods=['POST'])
def upload_loan_document(application_id):
    """
    Upload a document for a loan application
    """
    try:
        document_type = request.json.get('document_type')
        document_data = request.json.get('document_data')
        
        if not document_type or not document_data:
            return jsonify({
                "status": "error",
                "message": "Document type and data are required"
            }), 400
        
        result = document_processor.process_loan_document(application_id, document_type, document_data)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error uploading loan document: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error uploading loan document"
        }), 500

@app.route('/api/users/<int:user_id>/loans', methods=['GET'])
def get_user_loan_applications(user_id):
    """
    Get all loan applications for a user
    """
    try:
        applications = loan_service.get_user_applications(user_id)
        
        return jsonify({
            "status": "success",
            "applications": applications
        })
    except Exception as e:
        logging.error(f"Error retrieving user loan applications: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error retrieving user loan applications"
        }), 500

@app.route('/api/notifications/send', methods=['POST'])
def send_notification():
    """
    Send a notification to a user
    """
    try:
        user_id = request.json.get('user_id')
        notification_type = request.json.get('notification_type')
        message = request.json.get('message')
        
        if not user_id or not notification_type or not message:
            return jsonify({
                "status": "error",
                "message": "User ID, notification type, and message are required"
            }), 400
        
        # Implement notification service in a real application
        # For now, just log the notification
        logging.info(f"Sending {notification_type} notification to user {user_id}: {message}")
        
        return jsonify({
            "status": "success",
            "message": "Notification sent"
        })
    except Exception as e:
        logging.error(f"Error sending notification: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error sending notification"
        }), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit user feedback for a session
    """
    try:
        user_id = request.json.get('user_id')
        session_id = request.json.get('session_id')
        rating = request.json.get('rating')
        feedback_text = request.json.get('feedback_text', '')
        
        if not user_id or not session_id or rating is None:
            return jsonify({
                "status": "error",
                "message": "User ID, session ID, and rating are required"
            }), 400
        
        # Save feedback to database
        feedback_id = db_connector.save_feedback(user_id, session_id, rating, feedback_text)
        
        return jsonify({
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Feedback submitted successfully"
        })
    except Exception as e:
        logging.error(f"Error submitting feedback: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error submitting feedback"
        }), 500

@app.route('/api/analytics/session/<session_id>', methods=['GET'])
def get_session_analytics(session_id):
    """
    Get analytics for a specific session
    """
    try:
        analytics = video_service.get_session_analytics(session_id)
        
        return jsonify({
            "status": "success",
            "analytics": analytics
        })
    except Exception as e:
        logging.error(f"Error retrieving session analytics: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error retrieving session analytics"
        }), 500

@app.route('/api/users/<int:user_id>/recommendations', methods=['GET'])
def get_user_recommendations(user_id):
    """
    Get personalized product recommendations for a user
    """
    try:
        # This would typically involve a recommendation engine
        # For now, return placeholder recommendations
        recommendations = [
            {
                "product_id": 1,
                "product_name": "High Yield Savings Account",
                "description": "Earn higher interest on your savings",
                "confidence_score": 0.85
            },
            {
                "product_id": 3,
                "product_name": "Premium Credit Card",
                "description": "Earn rewards on every purchase",
                "confidence_score": 0.72
            }
        ]
        
        return jsonify({
            "status": "success",
            "recommendations": recommendations
        })
    except Exception as e:
        logging.error(f"Error getting recommendations: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error getting recommendations"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)