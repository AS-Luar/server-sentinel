#!/usr/bin/env python3
"""
Docker Container Monitoring Script
Part of server-sentinel monitoring system
Collects: All Docker containers with batch tracking
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
from shared.formatters import parse_memory_to_mb, calculate_uptime

# Configuration
CSV_HEADERS = ["batch", "timestamp", "container_name", "container_id", "image", 
               "memory_mb", "cpu_percent", "status", "uptime", "ports"]

#----------------------------------------------------------------


def collect_docker_containers(csv_path=None):
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
        timestamp = get_current_timestamp()
        batch_num = get_current_batch_number(csv_path) if csv_path else 1
        
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


#----------------------------------------------------------------


def main():
    """
    Main execution function
    Uses shared utilities for standardized execution flow
    """
    return handle_main_execution("Docker", collect_docker_containers, CSV_HEADERS, __file__, use_batches=True)

# Script execution
if __name__ == "__main__":
    exit(main())








