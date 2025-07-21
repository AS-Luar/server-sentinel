# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Server Sentinel is a system monitoring solution that collects metrics from servers, PM2 processes, and Docker containers. Data is stored in date-organized CSV files under each component's `data/` directory structure.

## Architecture

The system follows a modular architecture with three independent monitoring components:

### Core Components
- **server/**: Server hardware monitoring (CPU, RAM, disk, load average)
  - `system/collect-server.py`: Main monitoring script at server/system/collect-server.py:22
  - `data/`: CSV storage organized by date (YYYY/MM/YYYY-MM-DD.csv)

- **pm2/**: PM2 process monitoring with batch tracking
  - `system/collect-pm2.py`: PM2 data collection at pm2/system/collect-pm2.py:57
  - Uses batch numbering to group process snapshots
  - `data/`: CSV storage with same date structure

- **docker/**: Docker container monitoring with batch tracking  
  - `system/collect-docker.py`: Container metrics collection at docker/system/collect-docker.py:57
  - Includes memory parsing, port mapping, and uptime calculations
  - `data/`: CSV storage following same pattern

- **shared/**: Currently empty, intended for shared utilities

### Data Storage Pattern
All components use the same CSV storage structure:
```
{component}/data/YYYY/MM/YYYY-MM-DD.csv
```

### Key Functions
- **Batch tracking**: PM2 and Docker collectors use `get_current_batch_number()` to group related processes/containers collected in the same run
- **Memory parsing**: Docker collector includes `parse_memory_to_mb()` at docker/system/collect-docker.py:122 for converting various memory units
- **CSV handling**: All collectors automatically create directory structure and handle headers

## Running the Monitoring Scripts

Each monitoring script can be run independently:

```bash
# Server hardware monitoring
python3 server/system/collect-server.py

# PM2 process monitoring  
python3 pm2/system/collect-pm2.py

# Docker container monitoring
python3 docker/system/collect-docker.py
```

### Shared Utilities

The project uses a shared utilities system to eliminate code duplication:

- **shared/monitoring_utils.py**: Core monitoring functions (CSV operations, timestamps, batch tracking)
- **shared/formatters.py**: Data formatting utilities (memory parsing, uptime calculations)

All monitoring scripts import shared utilities using this pattern:
```python
# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import shared utilities
from shared.monitoring_utils import get_current_timestamp, handle_main_execution
from shared.formatters import parse_memory_to_mb, calculate_uptime
```

Scripts are designed to be run via cron jobs or schedulers. They:
- Print status information to stdout
- Return exit code 0 for success, 1 for failure
- Handle missing dependencies gracefully
- Create data directories automatically

## Dependencies

All scripts require Python 3 with standard library modules. External dependencies:
- `psutil` (server monitoring)
- `pm2` command available in PATH (PM2 monitoring)  
- `docker` command available in PATH (Docker monitoring)

## Data Format

### Server Metrics CSV
```
timestamp,cpu_percent,ram_used_mb,ram_percent,disk_percent,load_1min
```

### PM2 Processes CSV  
```
batch,timestamp,process_name,pm_id,instance,memory_mb,cpu_percent,status,restart_count,uptime_seconds
```

### Docker Containers CSV
```
batch,timestamp,container_name,container_id,image,memory_mb,cpu_percent,status,uptime,ports
```

## Best Practices

- Always use descriptive variable names