# v2/src/services/google.py
import os
import pickle
from typing import List, Dict, Any
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class GoogleIntegrationManager:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]
        self.creds = None
        self.drive_service = None
        self.gmail_service = None
        self.is_authenticated = False
        self.setup_google_services()
        
    def setup_google_services(self) -> bool:
        """Authenticate and setup Google services"""
        try:
            # Load token if exists
            if os.path.exists('google_token.pickle'):
                with open('google_token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)
            
            # Refresh or create new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if os.path.exists('credentials.json'):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            'credentials.json', self.SCOPES)
                        self.creds = flow.run_local_server(port=0)
                    else:
                        print("⚠️ credentials.json not found. Google integration disabled.")
                        return False
                
                # Save credentials
                with open('google_token.pickle', 'wb') as token:
                    pickle.dump(self.creds, token)
            
            # Build services
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.gmail_service = build('gmail', 'v1', credentials=self.creds)
            self.is_authenticated = True
            print("✅ Google services connected")
            return True
            
        except Exception as e:
            print(f"❌ Google setup error: {e}")
            self.is_authenticated = False
            return False

    def get_google_status(self) -> Dict[str, bool]:
        """Get status of Google services"""
        return {
            'authenticated': self.is_authenticated,
            'drive_available': self.drive_service is not None,
            'gmail_available': self.gmail_service is not None
        }

    def search_google_drive(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search Google Drive files"""
        if not self.drive_service:
            return []
            
        try:
            # Simple name search for now
            q = f"name contains '{query}' and trashed = false"
            results = self.drive_service.files().list(
                q=q, pageSize=limit, fields="files(id, name, mimeType)").execute()
            items = results.get('files', [])
            
            formatted = []
            for item in items:
                formatted.append({
                    'source': 'drive',
                    'file_name': item['name'],
                    'file_type': item['mimeType'],
                    'content': f"File ID: {item['id']}" # Placeholder for actual content
                })
            return formatted
        except Exception as e:
            print(f"❌ Drive search error: {e}")
            return []

    def search_gmail(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search Gmail messages"""
        if not self.gmail_service:
            return []
            
        try:
            results = self.gmail_service.users().messages().list(
                userId='me', q=query, maxResults=limit).execute()
            messages = results.get('messages', [])
            
            formatted = []
            for msg in messages:
                msg_detail = self.gmail_service.users().messages().get(
                    userId='me', id=msg['id']).execute()
                
                headers = msg_detail['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                snippet = msg_detail.get('snippet', '')
                
                formatted.append({
                    'source': 'gmail',
                    'subject': subject,
                    'from': sender,
                    'date': date,
                    'content': snippet
                })
            return formatted
        except Exception as e:
            print(f"❌ Gmail search error: {e}")
            return []
