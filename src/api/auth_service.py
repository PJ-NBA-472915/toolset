#!/usr/bin/env python3
"""
Authentication service for Nebula API
"""

import logging
from typing import Optional, Dict, Any
from .database import DatabaseManager
from datetime import datetime, timedelta
from fastapi import HTTPException
import subprocess

logger = logging.getLogger(__name__)

class AuthenticationService:
    """Manages authentication logic for the Nebula API"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize authentication service"""
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self.db_manager.is_authenticated()

    def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication information for display"""
        auth_data = self.db_manager.get_auth_data()
        if not auth_data:
            return {
                'authenticated': False,
                'user_id': None,
                'project_id': None,
                'auth_provider': None
            }
        
        return {
            'authenticated': True,
            'user_id': auth_data.get('user_id'),
            'project_id': auth_data.get('project_id'),
            'auth_provider': auth_data.get('auth_provider'),
            'last_updated': auth_data.get('updated_at'),
            'token_expires': auth_data.get('token_expires_at')
        }

    def authenticate_with_api_key(self, user_id: str, project_id: str, api_key: str) -> Dict[str, Any]:
        """Authenticate using API key"""
        if not user_id or not project_id or not api_key:
            raise HTTPException(status_code=400, detail="User ID, Project ID, and API Key are required")

        if not self._validate_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

        success = self.db_manager.store_auth_data(
            user_id=user_id,
            project_id=project_id,
            auth_provider='api_key',
            access_token=api_key,
            token_expires_at=datetime.now() + timedelta(days=30)
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to store authentication data")

        self.db_manager.log_action(
            user_id=user_id,
            action='login',
            details=f'API key authentication for project {project_id}'
        )

        return self.get_auth_status()

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key (placeholder implementation)"""
        # TODO: Implement actual API key validation
        return len(api_key) >= 10

    def logout(self, user_id: str) -> bool:
        """Logout user"""
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")

        auth_data = self.db_manager.get_auth_data(user_id=user_id)
        if not auth_data:
            raise HTTPException(status_code=404, detail="No active authentication to logout")

        self.db_manager.log_action(
            user_id=user_id,
            action='logout',
            details='User logged out'
        )

        return self.db_manager.logout(user_id)

    def authenticate_with_gcloud(self) -> Dict[str, Any]:
        """Authenticate using Google Cloud OAuth via gcloud CLI"""
        if not self._check_gcloud_available():
            raise HTTPException(status_code=500, detail="gcloud CLI is not available. Please install Google Cloud SDK.")

        if not self._is_gcloud_authenticated() or not self._is_gcloud_token_valid():
            try:
                subprocess.run(['gcloud', 'auth', 'login'], check=True, timeout=300)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                raise HTTPException(status_code=500, detail=f"gcloud authentication failed: {e}")

        return self._get_gcloud_credentials()

    def _check_gcloud_available(self) -> bool:
        try:
            subprocess.run(['gcloud', '--version'], capture_output=True, text=True, timeout=10, check=True)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False

    def _is_gcloud_authenticated(self) -> bool:
        try:
            result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'], capture_output=True, text=True, timeout=10, check=True)
            return result.stdout.strip() != ""
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False

    def _is_gcloud_token_valid(self) -> bool:
        try:
            subprocess.run(['gcloud', 'auth', 'print-access-token'], capture_output=True, text=True, timeout=10, check=True)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False

    def _get_gcloud_credentials(self) -> Dict[str, Any]:
        try:
            user_email_result = subprocess.run(['gcloud', 'config', 'get-value', 'account'], capture_output=True, text=True, timeout=10, check=True)
            user_email = user_email_result.stdout.strip()
            if not user_email:
                raise HTTPException(status_code=404, detail="No active gcloud account found")

            project_id_result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True, timeout=10)
            project_id = project_id_result.stdout.strip() if project_id_result.returncode == 0 else None

            if not project_id:
                raise HTTPException(status_code=404, detail="No gcloud project selected. Use 'gcloud config set project YOUR_PROJECT_ID'")

            access_token_result = subprocess.run(['gcloud', 'auth', 'print-access-token'], capture_output=True, text=True, timeout=10, check=True)
            access_token = access_token_result.stdout.strip()

            success = self.db_manager.store_auth_data(
                user_id=user_email,
                project_id=project_id,
                auth_provider='gcloud_oauth',
                access_token=access_token,
                token_expires_at=datetime.now() + timedelta(hours=1)
            )

            if not success:
                raise HTTPException(status_code=500, detail="Failed to store authentication data")

            self.db_manager.log_action(
                user_id=user_email,
                action='login',
                details=f'gcloud OAuth authentication for project {project_id}'
            )

            return self.get_auth_status()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            raise HTTPException(status_code=500, detail=f"Failed to get gcloud credentials: {e}")
