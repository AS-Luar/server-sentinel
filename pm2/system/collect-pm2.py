#!/usr/bin/env python3
"""
PM2 Process Monitoring Script
Part of server-sentinel monitoring system
Collects: All PM2 processes with batch tracking
"""

import json
import subprocess
import csv
from datetime import datetime, timezone
from pathlib import Path

# Configuration
script_dir = Path(__file__).parent
LOG_DIR = script_dir.parent / "data"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
CSV_HEADERS = ["batch", "timestamp", "process_name", "pm_id", "instance", 
               "memory_mb", "cpu_percent", "status", "restart_count", "uptime_seconds"]

#--------------------------------------------------------------

def get_current_batch_number():
    """
    Get the next batch number for today's CSV file
    Returns 1 for new files, or increments from last batch
    """
    try:
        # Get today's CSV path
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y/%m")
        filename = now.strftime("%Y-%m-%d.csv")
        csv_path = LOG_DIR / year_month / filename
        
        # If file doesn't exist, start with batch 1
        if not csv_path.exists():
            return 1
        
        # Read last line to get previous batch number
        with open(csv_path, 'r') as csvfile:
            lines = csvfile.readlines()
            if len(lines) <= 1:  # Only headers or empty
                return 1
            
            # Get last data line and extract batch number
            last_line = lines[-1].strip()
            if last_line:
                batch_num = int(last_line.split(',')[0])
                return batch_num + 1
            else:
                return 1
                
    except Exception as e:
        print(f"ERROR getting batch number: {e}")
        return 1

def collect_pm2_processes():
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
        timestamp = datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)
        batch_num = get_current_batch_number()
        
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

def write_pm2_data_to_csv(processes_data):
    """
    Write PM2 process data to daily CSV file
    Handles multiple processes per collection cycle
    """
    if not processes_data:
        print("No PM2 process data to write")
        return False
    
    try:
        # Create date-based file path
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y/%m")
        filename = now.strftime("%Y-%m-%d.csv")
        csv_path = LOG_DIR / year_month / filename
        
        # Create directory structure if needed
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists to determine if we need headers
        file_exists = csv_path.exists() and csv_path.stat().st_size > 0
        
        # Write data to CSV
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            
            # Write headers if this is a new file
            if not file_exists:
                writer.writeheader()
                print(f"Created new PM2 CSV file: {csv_path}")
            
            # Write all process data (multiple rows per collection)
            for process in processes_data:
                writer.writerow(process)
            
            print(f"Logged {len(processes_data)} PM2 processes to CSV")
        
        return True
        
    except Exception as e:
        print(f"ERROR writing PM2 data to CSV: {e}")
        return False

def main():
    """
    Main execution function
    Collects all PM2 process data and writes to CSV
    """
    print(f"Starting PM2 monitoring at {datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)} UTC")
    
    # Collect PM2 process data
    processes = collect_pm2_processes()
    
    if processes is not None:
        if len(processes) > 0:
            # Write to CSV
            success = write_pm2_data_to_csv(processes)
            
            if success:
                batch_num = processes[0]['batch']  # All processes have same batch
                print(f"Successfully logged batch {batch_num} with {len(processes)} processes")
                
                # Show summary of processes
                for proc in processes:
                    print(f"  {proc['process_name']} (ID:{proc['pm_id']}): {proc['memory_mb']}MB, {proc['cpu_percent']}% CPU, {proc['status']}")
            else:
                print("Failed to write PM2 data to CSV")
                return 1
        else:
            print("No PM2 processes running")
            return 0
    else:
        print("Failed to collect PM2 data")
        return 1
    
    return 0

# Script execution
if __name__ == "__main__":
    exit(main())

#------------------------------------------------------------------












