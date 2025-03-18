# document_processing_service.py
import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
from datetime import datetime
import json
import logging
from database_connector import DatabaseConnector

class DocumentProcessor:
    def __init__(self, db_connector=None):
        self.db_connector = db_connector or DatabaseConnector()
        self.logger = logging.getLogger(__name__)
        
    def capture_document(self, frame):
        """
        Process a video frame to detect and capture a document
        
        Args:
            frame: numpy array of the video frame
            
        Returns:
            dict: Status and captured document image if successful
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply adaptive threshold
            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find the largest contour (assumed to be the document)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Check if the contour is large enough to be a document
                if cv2.contourArea(largest_contour) > 50000:  # Adjust threshold as needed
                    # Approximate the contour to a polygon
                    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
                    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
                    
                    # If we have a quadrilateral, assume it's our document
                    if len(approx) == 4:
                        # Apply perspective transform to get a "birds-eye view"
                        pts = np.array([approx[0][0], approx[1][0], approx[2][0], approx[3][0]], dtype="float32")
                        rect = self._order_points(pts)
                        
                        # Get width and height of the document
                        (tl, tr, br, bl) = rect
                        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
                        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
                        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
                        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
                        
                        # Take the maximum of the width and height
                        maxWidth = max(int(widthA), int(widthB))
                        maxHeight = max(int(heightA), int(heightB))
                        
                        # Destination points for the transform
                        dst = np.array([
                            [0, 0],
                            [maxWidth - 1, 0],
                            [maxWidth - 1, maxHeight - 1],
                            [0, maxHeight - 1]], dtype="float32")
                        
                        # Compute the perspective transform matrix
                        M = cv2.getPerspectiveTransform(rect, dst)
                        
                        # Apply the transform
                        warped = cv2.warpPerspective(frame, M, (maxWidth, maxHeight))
                        
                        return {
                            "status": "success",
                            "document_image": warped
                        }
            
            return {
                "status": "no_document_detected",
                "message": "No document detected in frame"
            }
            
        except Exception as e:
            self.logger.error(f"Error capturing document: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing frame: {str(e)}"
            }
    
    def _order_points(self, pts):
        """
        Order points in top-left, top-right, bottom-right, bottom-left order
        """
        rect = np.zeros((4, 2), dtype="float32")
        
        # Top-left has smallest sum, bottom-right has largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right has smallest difference, bottom-left has largest difference
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect
    
    def identify_document_type(self, document_image):
        """
        Identify if the document is Aadhaar or PAN card
        
        Args:
            document_image: numpy array of the document image
            
        Returns:
            str: "aadhaar" or "pan" or "unknown"
        """
        # Convert to grayscale if it's not already
        if len(document_image.shape) == 3:
            gray = cv2.cvtColor(document_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = document_image
            
        # Apply preprocessing for better OCR
        gray = cv2.medianBlur(gray, 3)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Extract text using OCR
        text = pytesseract.image_to_string(Image.fromarray(gray))
        
        # Check for Aadhaar card
        if re.search(r'aadhaar|आधार|adhar|uid', text.lower()):
            return "aadhaar"
        
        # Check for PAN card
        if re.search(r'income tax|permanent account|pan|आयकर|पैन', text.lower()):
            return "pan"
        
        return "unknown"
    
    def extract_aadhaar_data(self, document_image):
        """
        Extract data from Aadhaar card
        
        Args:
            document_image: numpy array of the document image
            
        Returns:
            dict: Extracted data
        """
        # Convert to grayscale if it's not already
        if len(document_image.shape) == 3:
            gray = cv2.cvtColor(document_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = document_image
            
        # Apply preprocessing for better OCR
        gray = cv2.medianBlur(gray, 3)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Extract text using OCR
        text = pytesseract.image_to_string(Image.fromarray(gray))
        
        # Extract Aadhaar number
        aadhaar_number = None
        aadhaar_match = re.search(r'\d{4}\s\d{4}\s\d{4}', text)
        if aadhaar_match:
            aadhaar_number = aadhaar_match.group().replace(' ', '')
        
        # Extract name
        name = None
        name_pattern = re.search(r'(?:name|नाम)[:\s]*([A-Za-z\s]+)', text, re.IGNORECASE)
        if name_pattern:
            name = name_pattern.group(1).strip()
        
        # Extract DOB
        dob = None
        dob_pattern = re.search(r'(?:DOB|Date of Birth|जन्म तिथि)[:\s]*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
        if dob_pattern:
            dob = dob_pattern.group(1)
        
        # Extract address
        address = None
        address_pattern = re.search(r'(?:address|पता)[:\s]*(.+?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
        if address_pattern:
            address = address_pattern.group(1).strip()
        
        return {
            "document_type": "aadhaar",
            "aadhaar_number": aadhaar_number,
            "name": name,
            "dob": dob,
            "address": address
        }
    
    def extract_pan_data(self, document_image):
        """
        Extract data from PAN card
        
        Args:
            document_image: numpy array of the document image
            
        Returns:
            dict: Extracted data
        """
        # Convert to grayscale if it's not already
        if len(document_image.shape) == 3:
            gray = cv2.cvtColor(document_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = document_image
            
        # Apply preprocessing for better OCR
        gray = cv2.medianBlur(gray, 3)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Extract text using OCR
        text = pytesseract.image_to_string(Image.fromarray(gray))
        
        # Extract PAN number
        pan_number = None
        pan_match = re.search(r'[A-Z]{5}\d{4}[A-Z]', text)
        if pan_match:
            pan_number = pan_match.group()
        
        # Extract name
        name = None
        name_pattern = re.search(r'(?:name|नाम)[:\s]*([A-Za-z\s]+)', text, re.IGNORECASE)
        if name_pattern:
            name = name_pattern.group(1).strip()
        
        # Extract DOB
        dob = None
        dob_pattern = re.search(r'(?:DOB|Date of Birth|जन्म तिथि)[:\s]*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
        if dob_pattern:
            dob = dob_pattern.group(1)
        
        return {
            "document_type": "pan",
            "pan_number": pan_number,
            "name": name,
            "dob": dob
        }
    
    def save_document_data(self, user_id, document_data, document_image):
        """
        Save document data to database
        
        Args:
            user_id: ID of the user
            document_data: Extracted document data
            document_image: Document image
            
        Returns:
            bool: Success status
        """
        try:
            # Save document image to storage
            image_path = f"documents/{user_id}/{document_data['document_type']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            cv2.imwrite(image_path, document_image)
            
            # Prepare data for database
            if document_data["document_type"] == "aadhaar":
                doc_data = {
                    "user_id": user_id,
                    "document_type": "aadhaar",
                    "document_number": document_data.get("aadhaar_number"),
                    "verification_status": "pending",
                    "document_image_path": image_path
                }
                
                # Save to documents table
                document_id = self.db_connector.insert_document(doc_data)
                
                # Save user data if available
                if document_data.get("name") or document_data.get("dob"):
                    user_data = {
                        "user_id": user_id,
                        "full_name": document_data.get("name"),
                        "date_of_birth": document_data.get("dob")
                    }
                    self.db_connector.update_user(user_data)
                
                # Save address if available
                if document_data.get("address"):
                    address_data = {
                        "user_id": user_id,
                        "document_id": document_id,
                        "full_address": document_data.get("address"),
                        "is_current": True
                    }
                    self.db_connector.insert_address(address_data)
                
            elif document_data["document_type"] == "pan":
                doc_data = {
                    "user_id": user_id,
                    "document_type": "pan",
                    "document_number": document_data.get("pan_number"),
                    "verification_status": "pending",
                    "document_image_path": image_path
                }
                
                # Save to documents table
                document_id = self.db_connector.insert_document(doc_data)
                
                # Save user data if available
                if document_data.get("name") or document_data.get("dob"):
                    user_data = {
                        "user_id": user_id,
                        "full_name": document_data.get("name"),
                        "date_of_birth": document_data.get("dob")
                    }
                    self.db_connector.update_user(user_data)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving document data: {str(e)}")
            return False
    
    def process_document_frame(self, user_id, frame):
        """
        Process a video frame to detect, capture, and extract data from a document
        
        Args:
            user_id: ID of the user
            frame: numpy array of the video frame
            
        Returns:
            dict: Processing result
        """
        try:
            # Capture document
            capture_result = self.capture_document(frame)
            
            if capture_result["status"] != "success":
                return capture_result
            
            document_image = capture_result["document_image"]
            
            # Identify document type
            document_type = self.identify_document_type(document_image)
            
            if document_type == "unknown":
                return {
                    "status": "unknown_document",
                    "message": "Document type could not be identified"
                }
            
            # Extract data based on document type
            if document_type == "aadhaar":
                document_data = self.extract_aadhaar_data(document_image)
            elif document_type == "pan":
                document_data = self.extract_pan_data(document_image)
            
            # Save document data
            save_result = self.save_document_data(user_id, document_data, document_image)
            
            if not save_result:
                return {
                    "status": "error",
                    "message": "Failed to save document data"
                }
            
            return {
                "status": "success",
                "document_type": document_type,
                "extracted_data": document_data
            }
            
        except Exception as e:
            self.logger.error(f"Error processing document frame: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing document: {str(e)}"
            }