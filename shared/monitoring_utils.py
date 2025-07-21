#!/usr/bin/env python3
"""
Shared utilities for server-sentinel monitoring system
Centralized configuration, CSV operations, and common patterns
"""

from pathlib import Path
from datetime import datetime, timezone
import csv

# Global configuration
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

class MonitoringConfig:
    """Centralized configuration management for monitoring components"""
    
    def __init__(self, script_file):
        """Initialize config based on the calling script's location"""
        self.script_dir = Path(script_file).parent
        self.log_dir = self.script_dir.parent / "data"
        self.component_name = self.script_dir.parent.name
    
    def get_csv_path(self, timestamp=None):
        """Generate date-based CSV path following YYYY/MM/YYYY-MM-DD.csv pattern"""
        now = timestamp or datetime.now(timezone.utc)
        year_month = now.strftime("%Y/%m")
        filename = now.strftime("%Y-%m-%d.csv")
        return self.log_dir / year_month / filename

def get_current_timestamp():
    """Get formatted UTC timestamp using standard format"""
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)

def get_current_batch_number(csv_path):
    """
    Get next batch number for batch-tracked monitoring (PM2/Docker)
    Returns 1 for new files, or increments from last batch
    """
    try:
        if not csv_path.exists():
            return 1
        
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

class CSVWriter:
    """Handles CSV file operations with automatic directory setup and header management"""
    
    def __init__(self, csv_path, headers):
        """Initialize CSV writer with path and field headers"""
        self.csv_path = csv_path
        self.headers = headers
        # Extract component name from path structure for logging
        self.component_name = self.csv_path.parent.parent.parent.name
    
    def setup_file(self):
        """Create directory structure and check if file exists with content"""
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        return self.csv_path.exists() and self.csv_path.stat().st_size > 0
    
    def write_data(self, data):
        """
        Write data to CSV with automatic header handling
        Supports both single dict and list of dicts
        """
        if not data:
            print(f"No {self.component_name} data to write")
            return False
        
        try:
            file_exists = self.setup_file()
            
            with open(self.csv_path, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.headers)
                
                # Write headers if this is a new file
                if not file_exists:
                    writer.writeheader()
                    print(f"Created new {self.component_name} CSV file: {self.csv_path}")
                
                # Write data (handle both single dict and list)
                if isinstance(data, dict):
                    writer.writerow(data)
                    count = 1
                else:
                    for item in data:
                        writer.writerow(item)
                    count = len(data)
                
                print(f"Logged {count} {self.component_name} entries to CSV")
            
            return True
            
        except Exception as e:
            print(f"ERROR writing {self.component_name} data to CSV: {e}")
            return False

def handle_main_execution(component_name, collect_func, csv_headers, script_file, use_batches=False):
    """
    Standard main execution pattern for all monitoring scripts
    Handles the complete flow: collect → validate → write → report
    """
    print(f"Starting {component_name} monitoring at {get_current_timestamp()} UTC")
    
    # Initialize configuration and paths
    config = MonitoringConfig(script_file)
    csv_path = config.get_csv_path()
    
    # Collect data using the provided function
    data = collect_func(csv_path if use_batches else None)
    
    if data is not None:
        if data:  # Has data to write
            csv_writer = CSVWriter(csv_path, csv_headers)
            success = csv_writer.write_data(data)
            
            if success:
                # Print summary based on data type and batching
                if use_batches and isinstance(data, list) and len(data) > 0 and 'batch' in data[0]:
                    batch_num = data[0]['batch']
                    print(f"Successfully logged batch {batch_num} with {len(data)} {component_name} items")
                    
                    # Show individual item summaries for batched data
                    for item in data:
                        if component_name == "PM2":
                            print(f"  {item['process_name']} (ID:{item['pm_id']}): {item['memory_mb']}MB, {item['cpu_percent']}% CPU, {item['status']}")
                        elif component_name == "Docker":
                            print(f"  {item['container_name']}: {item['memory_mb']}MB, {item['cpu_percent']}% CPU, {item['status']}")
                else:
                    # Single metrics (server monitoring)
                    if isinstance(data, dict) and 'cpu_percent' in data:
                        print(f"Successfully logged metrics: CPU={data['cpu_percent']}%, RAM={data['ram_percent']}%, Disk={data['disk_percent']}%")
                    else:
                        print(f"Successfully logged {component_name} metrics")
                
                return 0
            else:
                print(f"Failed to write {component_name} data to CSV")
                return 1
        else:
            print(f"No {component_name} processes running" if use_batches else f"No {component_name} data available")
            return 0
    else:
        print(f"Failed to collect {component_name} data")
        return 1