#!/usr/bin/env python3
"""
Docker Container Monitoring Script
Part of server-sentinel monitoring system
Collects: All Docker containers with batch tracking
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
CSV_HEADERS = ["batch", "timestamp", "container_name", "container_id", "image", 
               "memory_mb", "cpu_percent", "status", "uptime", "ports"]

#----------------------------------------------------------------

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

def collect_docker_containers():
    """
    Collect data from all running Docker containers
    Returns: list of dictionaries with container data
    """
    try:
        # Run docker stats to get JSON data (single snapshot)
        result = subprocess.run(['docker', 'stats', '--format', 'json', '--no-stream'], 
                              capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            print(f"ERROR: docker command failed: {result.stderr}")
            return None
        
        # Parse JSON output (one JSON object per line)
        containers = []
        timestamp = datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)
        batch_num = get_current_batch_number()
        
        if not result.stdout.strip():
            print("No running Docker containers found")
            return []
        
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                container_data = json.loads(line)
                
                # Extract memory usage (remove units and convert to MB)
                memory_str = container_data.get('MemUsage', '0B / 0B')
                memory_used = memory_str.split(' / ')[0]
                memory_mb = parse_memory_to_mb(memory_used)
                
                # Extract CPU percentage (remove % sign)
                cpu_str = container_data.get('CPUPerc', '0.00%')
                cpu_percent = float(cpu_str.replace('%', ''))
                
                # Get additional container info
                container_info = get_container_details(container_data.get('Container', ''))
                
                container_record = {
                    'batch': batch_num,
                    'timestamp': timestamp,
                    'container_name': container_data.get('Name', 'unknown'),
                    'container_id': container_data.get('Container', 'unknown')[:12],  # Short ID
                    'image': container_info.get('image', 'unknown'),
                    'memory_mb': memory_mb,
                    'cpu_percent': round(cpu_percent, 1),
                    'status': container_info.get('status', 'unknown'),
                    'uptime': container_info.get('uptime', 'unknown'),
                    'ports': container_info.get('ports', 'none')
                }
                containers.append(container_record)
        
        return containers
        
    except subprocess.TimeoutExpired:
        print("ERROR: docker command timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR parsing docker JSON: {e}")
        return None
    except Exception as e:
        print(f"ERROR collecting Docker data: {e}")
        return None

def parse_memory_to_mb(memory_str):
    """
    Convert Docker memory string to MB
    Handles: 123.4MiB, 1.2GiB, 456KiB, etc.
    """
    try:
        # Remove whitespace and get numeric part
        memory_str = memory_str.strip()
        if memory_str.endswith('B'):
            memory_str = memory_str[:-1]  # Remove 'B'
        
        # Extract number and unit
        import re
        match = re.match(r'([0-9.]+)([A-Za-z]*)', memory_str)
        if not match:
            return 0.0
        
        value = float(match.group(1))
        unit = match.group(2).upper()
        
        # Convert to MB
        if unit in ['', 'B']:
            return round(value / (1024 * 1024), 1)
        elif unit in ['K', 'KB', 'KIB']:
            return round(value / 1024, 1)
        elif unit in ['M', 'MB', 'MIB']:
            return round(value, 1)
        elif unit in ['G', 'GB', 'GIB']:
            return round(value * 1024, 1)
        else:
            return 0.0
            
    except Exception:
        return 0.0

def get_container_details(container_id):
    """
    Get additional container details using docker inspect
    """
    try:
        result = subprocess.run(['docker', 'inspect', container_id], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return {'image': 'unknown', 'status': 'unknown', 'uptime': 'unknown', 'ports': 'none'}
        
        inspect_data = json.loads(result.stdout)[0]
        
        # Extract useful information
        image = inspect_data.get('Config', {}).get('Image', 'unknown')
        status = inspect_data.get('State', {}).get('Status', 'unknown')
        
        # Get port mappings
        port_bindings = inspect_data.get('NetworkSettings', {}).get('Ports', {})
        ports = []
        for container_port, host_bindings in port_bindings.items():
            if host_bindings:
                for binding in host_bindings:
                    host_port = binding.get('HostPort', '')
                    if host_port:
                        ports.append(f"{host_port}:{container_port}")
        
        ports_str = ','.join(ports) if ports else 'none'
        
        # Calculate uptime from start time
        started_at = inspect_data.get('State', {}).get('StartedAt', '')
        uptime = calculate_uptime(started_at) if started_at else 'unknown'
        
        return {
            'image': image,
            'status': status,
            'uptime': uptime,
            'ports': ports_str
        }
        
    except Exception:
        return {'image': 'unknown', 'status': 'unknown', 'uptime': 'unknown', 'ports': 'none'}

def calculate_uptime(started_at_str):
    """
    Calculate container uptime from start timestamp
    """
    try:
        from datetime import datetime
        # Parse Docker's timestamp format
        started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        uptime_delta = now - started_at
        
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
            
    except Exception:
        return 'unknown'

#----------------------------------------------------------------

def write_docker_data_to_csv(containers_data):
    """
    Write Docker container data to daily CSV file
    Handles multiple containers per collection cycle
    """
    if not containers_data:
        print("No Docker container data to write")
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
                print(f"Created new Docker CSV file: {csv_path}")
            
            # Write all container data (multiple rows per collection)
            for container in containers_data:
                writer.writerow(container)
            
            print(f"Logged {len(containers_data)} Docker containers to CSV")
        
        return True
        
    except Exception as e:
        print(f"ERROR writing Docker data to CSV: {e}")
        return False

def main():
    """
    Main execution function
    Collects all Docker container data and writes to CSV
    """
    print(f"Starting Docker monitoring at {datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)} UTC")
    
    # Collect Docker container data
    containers = collect_docker_containers()
    
    if containers is not None:
        if len(containers) > 0:
            # Write to CSV
            success = write_docker_data_to_csv(containers)
            
            if success:
                batch_num = containers[0]['batch']  # All containers have same batch
                print(f"Successfully logged batch {batch_num} with {len(containers)} containers")
                
                # Show summary of containers
                for container in containers:
                    print(f"  {container['container_name']}: {container['memory_mb']}MB, {container['cpu_percent']}% CPU, {container['status']}")
            else:
                print("Failed to write Docker data to CSV")
                return 1
        else:
            print("No Docker containers running")
            return 0
    else:
        print("Failed to collect Docker data")
        return 1
    
    return 0

# Script execution
if __name__ == "__main__":
    exit(main())








