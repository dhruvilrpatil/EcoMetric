"""
EcoMetric Backend — Firebase Admin SDK Initialization
Uses credentials from environment variables per PRD.
"""

import os
import json
from base64 import b64decode
import firebase_admin
from firebase_admin import credentials, firestore

def get_firebase_app():
    if not firebase_admin._apps:
        # Check if we have credentials in ENV
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        
        # In a real deployed app, we might use default credentials.
        # Here we try to parse the env vars if present, otherwise fall back to application default credentials.
        if project_id and os.getenv("FIREBASE_PRIVATE_KEY"):
            # Construct a credential dict from env vars
            private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n')
            
            cred_dict = {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
                "private_key": private_key,
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
                "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
                "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('FIREBASE_CLIENT_EMAIL', '')}"
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        elif os.getenv("FIRESTORE_EMULATOR_HOST"):
            # If using Firestore emulator
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": "demo-ecometric"})
        else:
            # Try application default credentials (e.g., in Google Cloud Run)
            try:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            except Exception:
                # Mock initialization for local dev if no real credentials are provided
                # In production this would fail hard, but for scaffolding we warn.
                import logging
                logging.warning("No Firebase credentials found. Proceeding with mock/empty credentials for local testing.")
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": "demo-ecometric",
                    "private_key_id": "dummy",
                    "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK\n-----END PRIVATE KEY-----\n",
                    "client_email": "mock@dummy.com",
                    "client_id": "dummy",
                    "auth_uri": "https://dummy",
                    "token_uri": "https://dummy"
                })
                try:
                    firebase_admin.initialize_app(cred)
                except Exception:
                    pass

    return firebase_admin.get_app()

def get_db():
    get_firebase_app()
    return firestore.client()
