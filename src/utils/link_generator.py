import os
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from base64 import urlsafe_b64encode
import json

class LinkGenerator:
    def __init__(self):
        # Generate or load encryption key
        self.key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
        self.fernet = Fernet(self.key)
        self.base_url = os.getenv('BASE_URL', 'http://localhost:8000')

    def generate_download_link(self, file_id: str, file_name: str) -> str:
        """
        Generate an encrypted download link that expires in 2 hours
        """
        expiry_time = datetime.utcnow() + timedelta(hours=2)
        
        # Create payload
        payload = {
            'file_id': file_id,
            'file_name': file_name,
            'expires': expiry_time.timestamp()
        }
        
        # Encrypt payload
        encrypted_data = self.fernet.encrypt(json.dumps(payload).encode())
        token = urlsafe_b64encode(encrypted_data).decode()
        
        return f"{self.base_url}/download/{token}"

    def verify_link(self, token: str) -> dict:
        """
        Verify and decrypt download link
        Returns: Dict with file_id and file_name if valid
        """
        try:
            encrypted_data = urlsafe_b64encode(token.encode())
            decrypted_data = self.fernet.decrypt(encrypted_data)
            payload = json.loads(decrypted_data)
            
            # Check expiration
            if datetime.fromtimestamp(payload['expires']) < datetime.utcnow():
                raise ValueError("Link has expired")
                
            return payload
        except Exception as e:
            raise ValueError(f"Invalid or expired link: {str(e)}")