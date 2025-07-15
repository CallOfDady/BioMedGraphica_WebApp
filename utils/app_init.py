"""
Application initialization script
Ensures proper setup of directories and temp file management
"""

import os
from pathlib import Path
from utils.temp_manager import get_temp_manager

def initialize_app():
    """Initialize the application with proper directory structure"""
    print("🚀 Initializing BioMedGraphica Web UI...")
    
    # Get the temp manager (this will create the temp directory)
    temp_manager = get_temp_manager()
    
    # Create other necessary directories
    project_root = Path(".")
    
    # Create cache directory if it doesn't exist
    cache_dir = project_root / "cache"
    cache_dir.mkdir(exist_ok=True)
    print(f"📁 Cache directory ready: {cache_dir}")
    
    # Create processed_data directory within cache
    processed_dir = cache_dir / "processed_data"
    processed_dir.mkdir(exist_ok=True)
    print(f"📁 Processed data directory ready: {processed_dir}")
    
    # Log initialization complete
    print("✅ Application initialization complete!")
    print(f"📊 Temp directory: {temp_manager.temp_dir}")
    print(f"📊 Cache directory: {cache_dir}")
    
    return temp_manager

if __name__ == "__main__":
    initialize_app()
