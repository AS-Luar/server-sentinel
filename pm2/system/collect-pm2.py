#!/usr/bin/env python3
"""
PM2 Process Monitoring Script
Part of server-sentinel monitoring system
Collects: All PM2 processes with batch tracking
"""

import json
import subprocess
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now this import will work:
from shared.monitoring_utils import get_current_timestamp, get_current_batch_number, handle_main_execution

# Configuration
CSV_HEADERS = ["batch", "timestamp", "process_name", "pm_id", "instance", 
               "memory_mb", "cpu_percent", "status", "restart_count", "uptime_seconds"]

#--------------------------------------------------------------


def collect_pm2_processes(csv_path=None):
    """
    Collect data from all PM2 processes
    Returns: list of dictionaries with process data
    """
    try:
        # Run pm2 jlist to get JSON data
        result = subprocess.run(['pm2', 'jlist'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"ERROR: pm2 command failed: {result.stderr}")
            return None
        
        # Parse JSON output
        pm2_data = json.loads(result.stdout)
        
        if not pm2_data:
            print("No PM2 processes found")
            return []
        
        # Extract metrics for each process
        processes = []
        timestamp = get_current_timestamp()
        batch_num = get_current_batch_number(csv_path) if csv_path else 1
        
        for proc in pm2_data:
            process_info = {
                'batch': batch_num,
                'timestamp': timestamp,
                'process_name': proc.get('name', 'unknown'),
                'pm_id': proc.get('pm_id', -1),
                'instance': proc.get('pm2_env', {}).get('instance_id', 0),
                'memory_mb': round(proc.get('monit', {}).get('memory', 0) / (1024 * 1024), 1),
                'cpu_percent': round(proc.get('monit', {}).get('cpu', 0), 1),
                'status': proc.get('pm2_env', {}).get('status', 'unknown'),
                'restart_count': proc.get('pm2_env', {}).get('restart_time', 0),
                'uptime_seconds': proc.get('pm2_env', {}).get('pm_uptime', 0)
            }
            processes.append(process_info)
        
        return processes
        
    except subprocess.TimeoutExpired:
        print("ERROR: pm2 command timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR parsing pm2 JSON: {e}")
        return None
    except Exception as e:
        print(f"ERROR collecting PM2 data: {e}")
        return None
    
#----------------------------------------------------------------


def main():
    """
    Main execution function
    Uses shared utilities for standardized execution flow
    """
    return handle_main_execution("PM2", collect_pm2_processes, CSV_HEADERS, __file__, use_batches=True)

# Script execution
if __name__ == "__main__":
    exit(main())

#------------------------------------------------------------------












