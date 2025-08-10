#!/usr/bin/env python3
"""
Formatting utilities for server-sentinel monitoring system
Handles data parsing and formatting tasks
"""

import re
from datetime import datetime, timezone

def parse_memory_to_mb(memory_str):
    """
    Convert Docker memory string to MB
    Handles various formats: 123.4MiB, 1.2GiB, 456KiB, 789B, etc.
    Returns float value in MB
    """
    try:
        # Remove whitespace
        memory_str = memory_str.strip()
        
        # Extract numeric value and unit using regex (handles 'B' suffix properly)
        match = re.match(r'([0-9.]+)([A-Za-z]*)', memory_str)
        if not match:
            return 0.0
        
        value = float(match.group(1))
        unit = match.group(2).upper()
        
        # Convert to MB based on unit
        if unit in ['', 'B']:
            return round(value / (1024 * 1024), 1)
        elif unit in ['K', 'KB', 'KIB']:
            return round(value / 1024, 1)
        elif unit in ['M', 'MB', 'MIB']:  # This will now match "MIB" correctly
            return round(value, 1)
        elif unit in ['G', 'GB', 'GIB']:
            return round(value * 1024, 1)
        else:
            return 0.0
            
    except Exception:
        return 0.0


def calculate_uptime(started_at_str):
    """
    Calculate container uptime from Docker's start timestamp
    Returns formatted uptime string (e.g., "2d 5h 30m", "3h 15m", "45m")
    """
    try:
        # Parse Docker's ISO format timestamp (handles both Z and +00:00 endings)
        started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        uptime_delta = now - started_at
        
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        # Format based on duration
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
            
    except Exception:
        return 'unknown'
