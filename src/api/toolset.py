from pathlib import Path

def get_toolset_info():
    """Return toolset information as a dictionary."""
    toolset_path = Path(__file__).parent.parent.parent
    tools_dir = toolset_path / "tools"
    tools = []
    
    if tools_dir.exists():
        for item in tools_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                if (item / "main.py").exists():
                    tools.append({"name": item.name, "status": "ready"})
                else:
                    tools.append({"name": item.name, "status": "incomplete"})
    
    other_dirs = []
    for item in toolset_path.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name not in ['tools', 'src', 'venv']:
            other_dirs.append(item.name)
            
    return {"tools": tools, "other_directories": other_dirs}
