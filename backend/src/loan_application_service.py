# loan_application_service.py
import json
import logging
from datetime import datetime
import uuid
from database_connector import DatabaseConnector

class LoanApplicationService:
    def __init__(self, db_connector=None):
        self.db_connector = db_connector or DatabaseConnector()
        self.logger = logging.getLogger(__name__)
    
    def start_application(self, user_id, loan_type):
        """
        Start a new loan application
        
        Args:
            user_id: ID of the user
            loan_type: Type of loan (personal, home, auto, etc.)
            
        Returns:
            dict: Application information
        """
        try:
            application_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            application_data = {
                "application_id": application_id,
                "user_id": user_id,
                "loan_type": loan_type,
                "start_time": timestamp,
                "status": "in_progress",
                "current_stage": "document_collection"
            }
            
            # Store application in database
            self.db_connector.insert_loan_application(application_data)
            
            return {
                "status": "success",
                "application_id": application_id,
                "message": "Loan application started successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error starting loan application: {str(e)}")
            return {
                "status": "error",
                "message": f"Error starting application: {str(e)}"
            }
    
    def update_application(self, application_id, update_data):
        """
        Update an existing loan application
        
        Args:
            application_id: ID of the application
            update_data: Dict containing update information
            
        Returns:
            dict: Result of updating the application
        """
        try:
            # Get current application data
            application = self.db_connector.get_loan_application(application_id)
            
            if not application:
                return {
                    "status": "error",
                    "message": "Application not found"
                }
            
            # Update application data
            for key, value in update_data.items():
                application[key] = value
            
            # Update last modified timestamp
            application["last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update database
            self.db_connector.update_loan_application(application)
            
            return {
                "status": "success",
                "message": "Application updated successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error updating loan application: {str(e)}")
            return {
                "status": "error",
                "message": f"Error updating application: {str(e)}"
            }
    
    def check_eligibility(self, application_id):
        """
        Check loan eligibility based on application data
        
        Args:
            application_id: ID of the application
            
        Returns:
            dict: Eligibility result
        """
        try:
            # Get application data
            application = self.db_connector.get_loan_application(application_id)
            
            if not application:
                return {
                    "status": "error",
                    "message": "Application not found"
                }
            
            # Get user data
            user = self.db_connector.get_user(application["user_id"])
            
            if not user:
                return {
                    "status": "error",
                    "message": "User not found"
                }
            
            # Get documents
            documents = self.db_connector.get_user_documents(application["user_id"])
            
            # Check if required documents are present
            has_aadhaar = any(doc["document_type"] == "aadhaar" for doc in documents)
            has_pan = any(doc["document_type"] == "pan" for doc in documents)
            
            if not (has_aadhaar and has_pan):
                return {
                    "status": "more_info",
                    "message": "Required documents are missing",
                    "missing_documents": [] if has_aadhaar else ["aadhaar"] + [] if has_pan else ["pan"]
                }
            
            # Get income details
            income_details = self.db_connector.get_income_details(application["user_id"])
            
            if not income_details:
                return {
                    "status": "more_info",
                    "message": "Income details are missing"
                }
            
            # Apply eligibility rules
            monthly_income = income_details.get("monthly_income", 0)
            loan_amount = application.get("loan_amount", 0)
            loan_tenure = application.get("loan_tenure", 0)
            
            # Basic eligibility check (this is a simplified example)
            # In a real system, you would have more complex rules
            if monthly_income < 15000:
                return {
                    "status": "rejected",
                    "message": "Monthly income below minimum requirement",
                    "reason": "low_income"
                }
            
            # Check loan amount vs income
            if loan_amount > monthly_income * 36:  # Example: max loan is 36x monthly income
                return {
                    "status": "rejected",
                    "message": "Loan amount exceeds maximum eligible amount",
                    "reason": "amount_too_high",
                    "max_eligible": monthly_income * 36
                }
            
            # Check age
            if user.get("date_of_birth"):
                dob = datetime.strptime(user["date_of_birth"], "%d/%m/%Y")
                age = (datetime.now() - dob).days // 365
                
                if age < 21 or age > 65:
                    return {
                        "status": "rejected",
                        "message": "Age not within eligible range (21-65 years)",
                        "reason": "age_not_eligible"
                    }
            
            # If all checks pass, mark as eligible
            eligible_amount = min(loan_amount, monthly_income * 36)
            interest_rate = 10.5  # Example: fixed rate
            
            # Calculate EMI
            r = interest_rate / (12 * 100)  # Monthly interest rate
            emi = (loan_amount * r * (1 + r) ** loan_tenure) / ((1 + r) ** loan_tenure - 1)
            
            eligibility_result = {
                "status": "approved",
                "message": "Loan application approved",
                "eligible_amount": eligible_amount,
                "interest_rate": interest_rate,
                "emi": round(emi, 2),
                "tenure": loan_tenure
            }
            
            # Update application status
            self.update_application(application_id, {
                "status": "approved",
                "eligibility_result": eligibility_result
            })
            
            return eligibility_result
            
        except Exception as e:
            self.logger.error(f"Error checking loan eligibility: {str(e)}")
            return {
                "status": "error",
                "message": f"Error checking eligibility: {str(e)}"
            }
    
    def submit_application(self, application_id):
        """
        Submit a loan application for final processing
        
        Args:
            application_id: ID of the application
            
        Returns:
            dict: Result of submitting the application
        """
        try:
            # Check eligibility first
            eligibility_result = self.check_eligibility(application_id)
            
            if eligibility_result["status"] != "approved":
                return eligibility_result
            
            # Get application data
            application = self.db_connector.get_loan_application(application_id)
            # Update application status
            application["status"] = "submitted"
            application["submission_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate application reference number
            reference_number = f"LOAN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            application["reference_number"] = reference_number
            
            # Update database
            self.db_connector.update_loan_application(application)
            
            # Create loan account (this would typically be done in a separate system)
            loan_account = {
                "application_id": application_id,
                "user_id": application["user_id"],
                "loan_type": application["loan_type"],
                "loan_amount": application["loan_amount"],
                "interest_rate": eligibility_result["interest_rate"],
                "tenure": application["loan_tenure"],
                "emi": eligibility_result["emi"],
                "status": "pending_disbursal",
                "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.db_connector.create_loan_account(loan_account)
            
            return {
                "status": "success",
                "message": "Loan application submitted successfully",
                "reference_number": reference_number,
                "next_steps": "Your loan application has been submitted. You will receive updates on your registered mobile number."
            }
            
        except Exception as e:
            self.logger.error(f"Error submitting loan application: {str(e)}")
            return {
                "status": "error",
                "message": f"Error submitting application: {str(e)}"
            }
    
    def get_application_status(self, application_id):
        """
        Get the current status of a loan application
        
        Args:
            application_id: ID of the application
            
        Returns:
            dict: Application status and details
        """
        try:
            # Get application data
            application = self.db_connector.get_loan_application(application_id)
            
            if not application:
                return {
                    "status": "error",
                    "message": "Application not found"
                }
            
            # Prepare status response
            status_response = {
                "status": "success",
                "application_status": application["status"],
                "application_details": {
                    "application_id": application["application_id"],
                    "loan_type": application["loan_type"],
                    "start_time": application["start_time"],
                    "current_stage": application["current_stage"]
                }
            }
            
            # Add additional details based on application status
            if application["status"] == "approved":
                status_response["application_details"]["eligibility_result"] = application.get("eligibility_result", {})
            
            if application["status"] == "submitted":
                status_response["application_details"]["reference_number"] = application.get("reference_number", "")
                status_response["application_details"]["submission_date"] = application.get("submission_date", "")
            
            return status_response
            
        except Exception as e:
            self.logger.error(f"Error getting application status: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting application status: {str(e)}"
            }