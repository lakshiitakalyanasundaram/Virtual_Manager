# database_connector.py
import mysql.connector
import json
import logging
from datetime import datetime
import os

class DatabaseConnector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection = None
        self.connect()
    
    def connect(self):
        """
        Connect to the MySQL database
        """
        try:
            self.connection = mysql.connector.connect(
                host=os.environ.get("DB_HOST", "localhost"),
                user=os.environ.get("DB_USER", "root"),
                password=os.environ.get("DB_PASSWORD", ""),
                database=os.environ.get("DB_NAME", "ai_branch_manager")
            )
            
            self.logger.info("Connected to database successfully")
        except Exception as e:
            self.logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    def _ensure_connection(self):
        """
        Ensure that the database connection is active
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
        except Exception as e:
            self.logger.error(f"Error reconnecting to database: {str(e)}")
            raise
    
    def insert_user(self, user_data):
        """
        Insert a new user into the database
        
        Args:
            user_data: Dict containing user information
            
        Returns:
            int: User ID
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
            INSERT INTO users (
                full_name, date_of_birth, phone_number, email, 
                registration_date, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                user_data.get("full_name", ""),
                user_data.get("date_of_birth", None),
                user_data.get("phone_number", ""),
                user_data.get("email", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "active"
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            
            user_id = cursor.lastrowid
            cursor.close()
            
            return user_id
            
        except Exception as e:
            self.logger.error(f"Error inserting user: {str(e)}")
            raise
    
    def update_user(self, user_data):
        """
        Update user information
        
        Args:
            user_data: Dict containing user information
            
        Returns:
            bool: Success status
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            # Build update query dynamically based on provided fields
            update_parts = []
            values = []
            
            if user_data.get("full_name"):
                update_parts.append("full_name = %s")
                values.append(user_data["full_name"])
            
            if user_data.get("date_of_birth"):
                update_parts.append("date_of_birth = %s")
                values.append(user_data["date_of_birth"])
            
            if user_data.get("phone_number"):
                update_parts.append("phone_number = %s")
                values.append(user_data["phone_number"])
            
            if user_data.get("email"):
                update_parts.append("email = %s")
                values.append(user_data["email"])
            
            if user_data.get("status"):
                update_parts.append("status = %s")
                values.append(user_data["status"])
            
            if not update_parts:
                return True  # Nothing to update
            
            query = f"""
            UPDATE users
            SET {", ".join(update_parts)}
            WHERE user_id = %s
            """
            
            values.append(user_data["user_id"])
            
            cursor.execute(query, values)
            self.connection.commit()
            
            cursor.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating user: {str(e)}")
            raise
    
    def get_user(self, user_id):
        """
        Get user information
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: User information
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT * FROM users WHERE user_id = %s
            """
            
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            
            cursor.close()
            
            return user
            
        except Exception as e:
            self.logger.error(f"Error getting user: {str(e)}")
            raise
    
    def insert_document(self, document_data):
        """
        Insert a new document into the database
        
        Args:
            document_data: Dict containing document information
            
        Returns:
            int: Document ID
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
            INSERT INTO documents (
                user_id, document_type, document_number, verification_status,
                document_image_path, upload_date
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                document_data["user_id"],
                document_data["document_type"],
                document_data.get("document_number", ""),
                document_data.get("verification_status", "pending"),
                document_data.get("document_image_path", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            
            document_id = cursor.lastrowid
            cursor.close()
            
            return document_id
            
        except Exception as e:
            self.logger.error(f"Error inserting document: {str(e)}")
            raise
    
    def get_user_documents(self, user_id):
        """
        Get documents for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            list: List of documents
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT * FROM documents WHERE user_id = %s
            """
            
            cursor.execute(query, (user_id,))
            documents = cursor.fetchall()
            
            cursor.close()
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting user documents: {str(e)}")
            raise
    
    def insert_address(self, address_data):
        """
        Insert a new address into the database
        
        Args:
            address_data: Dict containing address information
            
        Returns:
            int: Address ID
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
            INSERT INTO addresses (
                user_id, document_id, full_address, city, state, postal_code, is_current
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                address_data["user_id"],
                address_data.get("document_id", None),
                address_data["full_address"],
                address_data.get("city", ""),
                address_data.get("state", ""),
                address_data.get("postal_code", ""),
                address_data.get("is_current", True)
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            
            address_id = cursor.lastrowid
            cursor.close()
            
            return address_id
            
        except Exception as e:
            self.logger.error(f"Error inserting address: {str(e)}")
            raise
    
    def insert_income_details(self, income_data):
        """
        Insert income details into the database
        
        Args:
            income_data: Dict containing income information
            
        Returns:
            int: Income details ID
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
            INSERT INTO income_details (
                user_id, monthly_income, annual_income, employment_type, 
                employer_name, job_title, years_employed
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                income_data["user_id"],
                income_data.get("monthly_income", 0),
                income_data.get("annual_income", 0),
                income_data.get("employment_type", ""),
                income_data.get("employer_name", ""),
                income_data.get("job_title", ""),
                income_data.get("years_employed", 0)
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            
            income_id = cursor.lastrowid
            cursor.close()
            
            return income_id
            
        except Exception as e:
            self.logger.error(f"Error inserting income details: {str(e)}")
            raise
    
    def get_income_details(self, user_id):
        """
        Get income details for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: Income details
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT * FROM income_details WHERE user_id = %s
            """
            
            cursor.execute(query, (user_id,))
            income_details = cursor.fetchone()
            
            cursor.close()
            
            return income_details
            
        except Exception as e:
            self.logger.error(f"Error getting income details: {str(e)}")
            raise
    
    def insert_session(self, session_data):
        """
        Insert a new session into the database
        
        Args:
            session_data: Dict containing session information
            
        Returns:
            bool: Success status
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
            INSERT INTO sessions (
                session_id, user_id, start_time, status, conversation_stage
            ) VALUES (%s, %s, %s, %s, %s)
            """
            
            values = (
                session_data["session_id"],
                session_data["user_id"],
                session_data["start_time"],
                session_data["status"],
                session_data["conversation_stage"]
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            
            cursor.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting session: {str(e)}")
            raise
    
    def update_session(self, session_data):
        """
        Update session information
        
        Args:
            session_data: Dict containing session information
            
        Returns:
            bool: Success status
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
            UPDATE sessions
            SET status = %s, conversation_stage = %s
            WHERE session_id = %s
            """
            
            values = (
                session_data["status"],
                session_data["conversation_stage"],
                session_data["session_id"]
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            
            cursor.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating session: {str(e)}")
            raise
    
    def insert_response(self, response_data):
        """
        Insert a user response into the database
        
        Args:
            response_data: Dict containing response information
            
        Returns:
            int: Response ID
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
            INSERT INTO responses (
                session_id, question_id, response_path, timestamp,
                duration, transcription
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                response_data["session_id"],
                response_data["question_id"],
                response_data["response_path"],
                response_data["timestamp"],
                response_data.get("duration", 0),
                response_data.get("transcription", "")
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            
            response_id = cursor.lastrowid
            cursor.close()
            
            return response_id
            
        except Exception as e:
            self.logger.error(f"Error inserting response: {str(e)}")
            raise
    
    def get_next_interaction(self, current_stage):
        """
        Get the next interaction based on the current conversation stage
        
        Args:
            current_stage: Current conversation stage
            
        Returns:
            dict: Next interaction details
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT * FROM interactions
            WHERE trigger_stage = %s
            ORDER BY sequence_number ASC
            LIMIT 1
            """
            
            cursor.execute(query, (current_stage,))
            interaction = cursor.fetchone()
            
            cursor.close()
            
            return interaction
            
        except Exception as e:
            self.logger.error(f"Error getting next interaction: {str(e)}")
            raise
    
    def insert_loan_application(self, application_data):
        """
        Insert a new loan application into the database
        
        Args:
            application_data: Dict containing application information
            
        Returns:
            bool: Success status
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
            INSERT INTO loan_applications (
                application_id, user_id, loan_type, start_time,
                status, current_stage
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                application_data["application_id"],
                application_data["user_id"],
                application_data["loan_type"],
                application_data["start_time"],
                application_data["status"],
                application_data["current_stage"]
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            
            cursor.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting loan application: {str(e)}")
            raise
    
    def get_loan_application(self, application_id):
        """
        Get loan application information
        
        Args:
            application_id: ID of the application
            
        Returns:
            dict: Application information
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT * FROM loan_applications WHERE application_id = %s
            """
            
            cursor.execute(query, (application_id,))
            application = cursor.fetchone()
            
            cursor.close()
            
            return application
            
        except Exception as e:
            self.logger.error(f"Error getting loan application: {str(e)}")
            raise
    
    def update_loan_application(self, application_data):
        """
        Update loan application information
        
        Args:
            application_data: Dict containing application information
            
        Returns:
            bool: Success status
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            # Build update query dynamically based on provided fields
            update_parts = []
            values = []
            
            for key, value in application_data.items():
                if key != "application_id" and key != "eligibility_result":
                    update_parts.append(f"{key} = %s")
                    values.append(value)
            
            # Handle eligibility result separately
            if "eligibility_result" in application_data:
                update_parts.append("eligibility_result = %s")
                values.append(json.dumps(application_data["eligibility_result"]))
            
            if not update_parts:
                return True  # Nothing to update
            
            query = f"""
            UPDATE loan_applications
            SET {", ".join(update_parts)}
            WHERE application_id = %s
            """
            
            values.append(application_data["application_id"])
            
            cursor.execute(query, values)
            self.connection.commit()
            
            cursor.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating loan application: {str(e)}")
            raise
    
    def create_loan_account(self, loan_account_data):
        """
        Create a new loan account
        
        Args:
            loan_account_data: Dict containing loan account information
            
        Returns:
            int: Loan account ID
        """
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
            INSERT INTO loan_accounts (
                application_id, user_id, loan_type, loan_amount,
                interest_rate, tenure, emi, status, creation_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                loan_account_data["application_id"],
                loan_account_data["user_id"],
                loan_account_data["loan_type"],
                loan_account_data["loan_amount"],
                loan_account_data["interest_rate"],
                loan_account_data["tenure"],
                loan_account_data["emi"],
                loan_account_data["status"],
                loan_account_data["creation_date"]
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            
            loan_account_id = cursor.lastrowid
            cursor.close()
            
            return loan_account_id
            
        except Exception as e:
            self.logger.error(f"Error creating loan account: {str(e)}")
            raise
    
    def close(self):
        """
        Close the database connection
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.info("Database connection closed")