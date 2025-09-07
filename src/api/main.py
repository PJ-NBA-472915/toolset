#!/usr/bin/env python3

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Any, List, Optional
from .system import get_system_info
from .toolset import get_toolset_info
from .auth_service import AuthenticationService
from .database import DatabaseManager
from .tool_service import ToolService
from .ssh_config_service import SSHConfigService

app = FastAPI()

db_manager = DatabaseManager()
auth_service = AuthenticationService(db_manager)
tool_service = ToolService()
ssh_config_service = SSHConfigService()

class LoginRequest(BaseModel):
    user_id: str
    project_id: str
    api_key: str

class LogoutRequest(BaseModel):
    user_id: str

class SetConfigRequest(BaseModel):
    key: str
    value: Any

class RunToolRequest(BaseModel):
    args: Optional[List[str]] = None

class SSHHost(BaseModel):
    host: str
    hostname: str
    user: str
    key_path: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Nebula API"}

@app.get("/system/info")
def system_info():
    """Return system information."""
    return get_system_info()

@app.get("/toolset/info")
def toolset_info():
    """Return toolset information."""
    return get_toolset_info()

@app.get("/auth/status")
def auth_status():
    """Return authentication status."""
    return auth_service.get_auth_status()

@app.post("/auth/login")
def login(request: LoginRequest):
    """Authenticate with API key."""
    return auth_service.authenticate_with_api_key(request.user_id, request.project_id, request.api_key)

@app.post("/auth/login/gcloud")
def login_gcloud():
    """Authenticate with gcloud."""
    return auth_service.authenticate_with_gcloud()

@app.post("/auth/logout")
def logout(request: LogoutRequest):
    """Logout user."""
    return {"success": auth_service.logout(request.user_id)}

@app.get("/config")
def get_all__config():
    """Get all configuration settings."""
    return db_manager.get_all_config()

@app.get("/config/{key}")
def get_config(key: str):
    """Get a specific configuration setting."""
    return {"key": key, "value": db_manager.get_config(key)}

@app.post("/config")
def set_config(request: SetConfigRequest):
    """Set a configuration value."""
    return {"success": db_manager.set_config(request.key, request.value)}

@app.post("/tools/{tool_name}/run")
def run_tool(tool_name: str, request: RunToolRequest):
    """Run a tool."""
    return tool_service.run_tool(tool_name, request.args)

@app.get("/ssh/hosts")
def get_ssh_hosts():
    """Get all SSH hosts."""
    return ssh_config_service.get_all_hosts()

@app.post("/ssh/hosts")
def add_ssh_host(host: SSHHost):
    """Add a new SSH host."""
    return ssh_config_service.add_host(host.host, host.hostname, host.user, host.key_path)

@app.put("/ssh/hosts/{host_name}")
def update_ssh_host(host_name: str, host: SSHHost):
    """Update an existing SSH host."""
    return ssh_config_service.update_host(host_name, host.hostname, host.user, host.key_path)
