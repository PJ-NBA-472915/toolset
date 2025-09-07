import sys
import os

def get_system_info():
    """Return system information as a dictionary."""
    return {
        "python_version": sys.version.split()[0],
        "working_directory": os.getcwd(),
        "user": os.getenv('USER', 'unknown'),
        "platform": sys.platform
    }
