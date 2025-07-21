#!/usr/bin/env python3
"""
Import helper for server-sentinel shared utilities
Provides a robust way to import shared modules from any script location
"""

import sys
from pathlib import Path

def setup_shared_imports():
    """
    Add the shared directory to Python path for importing utilities.
    This function can be called from any script in the project structure.
    """
    # Get the project root directory (assumes shared/ is at project root)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent  # Go up from shared/ to project root
    shared_dir = project_root / "shared"
    
    # Add to Python path if not already present
    shared_path = str(shared_dir)
    if shared_path not in sys.path:
        sys.path.insert(0, shared_path)
    
    return shared_dir

# Alternative approach: direct imports with error handling
def safe_import_monitoring_utils():
    """
    Safely import monitoring utilities with helpful error messages
    """
    try:
        setup_shared_imports()
        from monitoring_utils import (
            get_current_timestamp, 
            get_current_batch_number, 
            handle_main_execution,
            MonitoringConfig,
            CSVWriter
        )
        return {
            'get_current_timestamp': get_current_timestamp,
            'get_current_batch_number': get_current_batch_number,
            'handle_main_execution': handle_main_execution,
            'MonitoringConfig': MonitoringConfig,
            'CSVWriter': CSVWriter
        }
    except ImportError as e:
        print(f"ERROR: Cannot import monitoring utilities: {e}")
        print(f"Expected shared directory at: {Path(__file__).parent}")
        print("Please ensure shared/monitoring_utils.py exists")
        raise

def safe_import_formatters():
    """
    Safely import formatter utilities with helpful error messages
    """
    try:
        setup_shared_imports()
        from formatters import parse_memory_to_mb, calculate_uptime
        return {
            'parse_memory_to_mb': parse_memory_to_mb,
            'calculate_uptime': calculate_uptime
        }
    except ImportError as e:
        print(f"ERROR: Cannot import formatter utilities: {e}")
        print(f"Expected shared directory at: {Path(__file__).parent}")
        print("Please ensure shared/formatters.py exists")
        raise