#!/usr/bin/env python3
"""
Nebula API Management CLI
"""

import typer
import uvicorn
import os
import inquirer
import sys
from pathlib import Path

app = typer.Typer()

def start_service(host: str = "127.0.0.1", port: int = 8000):
    """Start the Nebula API service."""
    typer.echo(f"Starting Nebula API service on {host}:{port}")
    # This is a workaround to make sure that the `api` module can be found.
    sys.path.insert(0, str(Path(__file__).parent.parent))
    uvicorn.run("api.main:app", host=host, port=port, reload=True)

@app.command()
def start(host: str = "127.0.0.1", port: int = 8000):
    """Start the Nebula API service."""
    start_service(host, port)

@app.command()
def stop():
    """Stop the Nebula API service."""
    typer.echo("Stopping Nebula API service (not yet implemented)")

@app.command()
def logs():
    """Tail the Nebula API service logs."""
    typer.echo("Tailing logs (not yet implemented)")

@app.command()
def interactive():
    """Run in interactive mode."""
    while True:
        questions = [
            inquirer.List(
                'action',
                message="What would you like to do?",
                choices=['Start Service', 'Stop Service', 'View Logs', 'Exit'],
            ),
        ]
        answers = inquirer.prompt(questions)
        if not answers or answers['action'] == 'Exit':
            break
        
        action = answers['action']

        if action == 'Start Service':
            start_service()
        elif action == 'Stop Service':
            stop()
        elif action == 'View Logs':
            logs()

def main():
    # This is a workaround to make sure that the `api` module can be found.
    sys.path.insert(0, str(Path(__file__).parent.parent))
    # If no command is specified, run in interactive mode
    if len(sys.argv) == 1:
        interactive()
    else:
        app()

if __name__ == "__main__":
    main()
