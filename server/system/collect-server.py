#!/usr/bin/env python3
"""
Server Hardware Monitoring Script
Part of server-sentinel monitoring system
Collects: CPU, RAM, Disk, Load Average
"""

import psutil
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

# Configuration
script_dir = Path(__file__).parent
LOG_DIR = script_dir.parent / "data" #Always finds data folder, Local development path
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
CSV_HEADERS = ["timestamp", "cpu_percent", "ram_used_mb", "ram_percent", "disk_percent", "load_1min"]

#----------------------------------------------------------

def collect_system_metrics():
    """
    Collect current system metrics
    Returns: dictionary with metric names and values
    """
    try:
        # Get current timestamp
        timestamp = datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)
        
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

def write_metrics_to_csv(metrics_data):
    """
    Write metrics to daily CSV file
    Creates directory structure and handles CSV headers automatically
    """
    if metrics_data is None:
        print("No metrics to write")
        return False
    
    try:
        # Create date-based file path: data/2025/07/2025-07-20.csv
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y/%m")
        filename = now.strftime("%Y-%m-%d.csv")
        
        csv_path = LOG_DIR / year_month / filename
        
        # Create directory structure if it doesn't exist
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists to determine if we need headers
        file_exists = csv_path.exists()
        
        # Write data to CSV
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            
            # Write headers if this is a new file
            if not file_exists:
                writer.writeheader()
                print(f"Created new CSV file: {csv_path}")
            
            # Write the metrics data
            writer.writerow(metrics_data)
            
        return True
        
    except Exception as e:
        print(f"ERROR writing to CSV: {e}")
        return False

#-----------------------------------------------------------------------

def main():
    """
    Main execution function
    Collects metrics and writes to CSV
    """
    print(f"Starting metric collection at {datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)} UTC")
    
    # Collect system metrics
    metrics = collect_system_metrics()
    
    if metrics:
        # Write to CSV
        success = write_metrics_to_csv(metrics)
        
        if success:
            print(f"Successfully logged metrics: CPU={metrics['cpu_percent']}%, RAM={metrics['ram_percent']}%, Disk={metrics['disk_percent']}%")
        else:
            print("Failed to write metrics to CSV")
            return 1
    else:
        print("Failed to collect metrics")
        return 1
    
    return 0

# Script execution
if __name__ == "__main__":
    exit(main())














