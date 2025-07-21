#!/usr/bin/env python3
"""
Server Hardware Monitoring Script
Part of server-sentinel monitoring system
Collects: CPU, RAM, Disk, Load Average
"""

import psutil
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now this import will work:
from shared.monitoring_utils import get_current_timestamp, handle_main_execution

# Configuration
CSV_HEADERS = ["timestamp", "cpu_percent", "ram_used_mb", "ram_percent", "disk_percent", "load_1min"]

#----------------------------------------------------------

def collect_system_metrics(csv_path=None):
    """
    Collect current system metrics
    Returns: dictionary with metric names and values
    """
    try:
        # Get current timestamp
        timestamp = get_current_timestamp()
        
        # CPU percentage (1 second sample for accuracy)
        cpu_percent = round(psutil.cpu_percent(interval=1), 1)
        
        # Memory statistics
        memory = psutil.virtual_memory()
        ram_used_mb = round(memory.used / (1024 * 1024), 1)  # Convert bytes to MB
        ram_percent = round(memory.percent, 1)
        
        # Disk usage for root partition
        disk = psutil.disk_usage('/')
        disk_percent = round(disk.percent, 1)
        
        # Load average (1-minute value)
        load_avg = psutil.getloadavg()
        load_1min = round(load_avg[0], 2)
        
        return {
            'timestamp': timestamp,
            'cpu_percent': cpu_percent,
            'ram_used_mb': ram_used_mb,
            'ram_percent': ram_percent,
            'disk_percent': disk_percent,
            'load_1min': load_1min
        }
        
    except Exception as e:
        print(f"ERROR collecting metrics: {e}")
        return None

#--------------------------------------------------------------------


#-----------------------------------------------------------------------

def main():
    """
    Main execution function
    Uses shared utilities for standardized execution flow
    """
    return handle_main_execution("server", collect_system_metrics, CSV_HEADERS, __file__)

# Script execution
if __name__ == "__main__":
    exit(main())

