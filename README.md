# Grafana and Gatling Report Automation

## Overview

This project automates the downloading of Gatling performance test reports and Grafana metrics. It uses a flexible, configuration-based approach to support multiple services and metrics.

## Features

- 🚀 **Automatic Gatling Report Download:** SSH-based downloading of latest performance test reports
- 📊 **Grafana Metrics Collection:** API-based downloading of performance metrics as images
- ⚙️ **Flexible Configuration:** YAML-based configuration for easy customization
- 🔧 **Service Management:** Enable/disable services individually
- 📝 **Comprehensive Logging:** Detailed logging with multiple levels
- 🕐 **Timezone Support:** Automatic timezone conversion for time ranges
- 📁 **Organized Output:** Structured folder organization for reports and metrics

## Project Structure

```
reportsScript/
├── config.yml              # Main configuration file
├── metrics_urls.yml        # Grafana metrics configuration
├── requirements.txt        # Python dependencies
├── example_usage.py        # Configuration management demo
├── grafana_enhanced.py     # Enhanced Grafana features
├── get_screenshots.sh      # Shell wrapper script
├── config_manager.py       # Configuration management utilities
├── grafana_report.py       # Alternative Grafana report handler
├── test_url.py            # URL generation testing
├── src/
│   ├── main.py             # Entry point
│   ├── config.py           # Configuration loader
│   ├── config_loader.py    # Metrics configuration loader
│   ├── ssh_service.py      # SSH service for Gatling reports
│   ├── grafana_service.py  # Grafana API service
│   └── utils.py            # Utility functions
└── tests/                  # Unit tests
    ├── test_config_loader.py
    ├── test_grafana_service.py
    └── test_utils.py
```

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the script:**
   - Edit `config.yml` with your settings
   - Modify `metrics_urls.yml` if needed

## Configuration

### Main Configuration (`config.yml`)

```yaml
mainConfig:
  scenario: "Upload_file"                    # Test scenario name
  type_of_script: "Maxperf"                  # Script type
  from: "2025-07-31 13:03:44.562"           # Start time
  to: "2025-07-31 15:16:09.381"             # End time
  timezone: "Europe/Moscow"                  # Timezone for time conversion

main_folder: "/path/to/reports"              # Base folder for all reports

services:
  # System services
  ssh_service: true                          # Enable SSH service
  grafana_service: true                      # Enable Grafana service
  gatling_metrics_service: true              # Enable Gatling metrics from secondary Grafana
  
  # Application services (enable only what you need)
  dh-registry-service: true
  dh-documents-service: true
  dh-files-service: true
  dh-auth-service: false
  # ... add more services as needed

ssh_config:
  host: "172.19.93.113"
  username: "tester"
  password: "123456"
  remote_path: "/home/tester/Gatling/dh-nt-gatling/target/gatling"
  local_path: "./reports/gatling"

grafana:
  local_path: "./reports/metrics"
  metrics_config: "metrics_urls.yml"
  api_key: "Bearer your_api_key_here"
  timezone: "Europe/Moscow"
  base_url: "https://grafana.your-domain.com"

# Secondary Grafana configuration for Gatling metrics
gatling_grafana:
  local_path: "./reports/metrics/gatling_metrics"
  base_url: "http://172.19.93.116:3000"
  api_key: "Bearer your_api_key_here"
  timezone: "Europe/Moscow"
  script_name: "Attribute_Search_2"           # Script name for Gatling tests
  gatling_metrics_config: "gatling_metrics_urls.yml"
```

### Metrics Configuration (`metrics_urls.yml`)

Defines all available metrics that can be downloaded from Grafana. Each metric includes:
- Dashboard information (UID, name, panel ID)
- Image dimensions
- Variables (with PLACEHOLDER for automatic service name substitution)

## Usage

### Basic Commands

```bash
# Run from the src/ directory
cd src

# Download both Gatling reports and Grafana metrics
python3 main.py -gatling -grafana

# Download only Grafana metrics
python3 main.py -grafana

# Download only Gatling reports
python3 main.py -gatling

# Show help
python3 main.py --help
```

### Alternative: Run from project root

```bash
# Run from project root directory
python3 src/main.py -grafana
```

## Available Metrics

The script supports downloading various performance metrics:

### Spring Boot Metrics
- **cpu_usage** - Application CPU usage
- **load_average** - System load average
- **threads** - Thread count
- **classes_loaded/unloaded** - Class loading statistics

### Memory Metrics
- **eden_space** - G1 Eden Space (heap)
- **old_gen** - G1 Old Generation (heap)
- **survivor_space** - G1 Survivor Space (heap)
- **metaspace** - Metaspace (non-heap)
- **compressed_class_space** - Compressed class space
- **memory_allocate_promote** - Memory allocation/promotion

### Garbage Collection
- **gc_count** - GC cycle count
- **gc_stop_the_world_duration** - Stop-the-world GC duration

### HTTP Metrics
- **http_codes** - HTTP response code distribution
- **requests_per_second** - Request rate
- **requests_duration** - Request duration

### Kubernetes Metrics
- **cpu_by_pod** - CPU usage by pod
- **memory_usage_by_pods** - Memory usage by pod

### Gatling Metrics (from Secondary Grafana)
- **panel_3** - Gatling dashboard panel 3
- **panel_9** - Gatling dashboard panel 9
- **panel_1** - Gatling dashboard panel 1
- **panel_6** - Gatling dashboard panel 6
- **panel_7** - Gatling dashboard panel 7
- **panel_4** - Gatling dashboard panel 4

## Output Structure

The script creates an organized folder structure based on your configuration:

```
reports/
├── gatling/
│   └── [gatling-report-folder]/
└── metrics/
    ├── gatling_metrics/              # Gatling dashboard metrics
    │   ├── panel_3.png
    │   ├── panel_9.png
    │   ├── panel_1.png
    │   ├── panel_6.png
    │   ├── panel_7.png
    │   └── panel_4.png
    ├── dh-documents-service/
    │   ├── cpu_usage.png
    │   ├── memory_usage.png
    │   └── ...
    ├── dh-files-service/
    │   ├── cpu_usage.png
    │   └── ...
    └── ...
```

## Adding New Services

1. **Add service to `config.yml`:**
   ```yaml
   services:
     # ... existing services ...
     my-new-service: true
   ```

2. **Run the script** - metrics will be automatically downloaded for the new service

## Adding New Metrics

1. **Find the Grafana panel information:**
   - Dashboard UID
   - Panel ID
   - Required variables

2. **Add to `metrics_urls.yml`:**
   ```yaml
   - name: "my_new_metric"
     dashboard_uid: "dashboard-uid"
     dashboard_name: "dashboard-name"
     orgId: 1
     panelId: 123
     width: 1000
     height: 500
     vars:
       var-application: "PLACEHOLDER"  # Will be replaced with service name
       # ... other variables ...
   ```

## Auxiliary Scripts

### example_usage.py
This script demonstrates:
- How to update the time range in the configuration
- How to manage and activate application services
- Lists available metrics

To run the example:
```bash
python3 example_usage.py
```

### grafana_enhanced.py
Provides additional Grafana automation features:
- Validate Grafana API connection
- Test individual metrics
- Batch download with progress tracking

To run the enhanced script:
```bash
python3 grafana_enhanced.py --test-connection
```

### get_screenshots.sh
A shell script wrapper for managing Grafana screenshots.

Usage:
```bash
./get_screenshots.sh download   # Download all screenshots
./get_screenshots.sh test       # Test Grafana API connection
./get_screenshots.sh list       # List all available metrics
./get_screenshots.sh single cpu_usage   # Test single metric
```

### Additional Utilities

- **config_manager.py** - Configuration management utilities for loading and formatting YAML configurations
- **grafana_report.py** - Alternative Grafana report handler with simplified interface
- **test_url.py** - URL generation testing script for debugging Grafana API calls

## Logging

- **File logging:** All operations are logged to `app.log`
- **Console logging:** Important messages displayed in terminal
- **Log levels:** INFO, WARNING, ERROR for different types of messages

## Troubleshooting

### Common Issues

1. **"File not found: config.yml"**
   - Ensure you're running from the correct directory
   - Check that config.yml exists

2. **SSH connection failed**
   - Verify SSH credentials in config.yml
   - Check network connectivity to SSH host

3. **Grafana API errors**
   - Verify API key is correct and has proper permissions
   - Check Grafana base URL
   - Ensure dashboard UIDs and panel IDs are correct

4. **No metrics downloaded**
   - Check that services are enabled in config.yml
   - Verify time range is valid
   - Check Grafana service is enabled

### Getting Help

```bash
# Check script help
python3 src/main.py --help

# View logs for detailed error information
tail -f app.log
```

## Requirements

- Python 3.6 or higher
- Network access to SSH server (for Gatling reports)
- Network access to Grafana instance
- Valid Grafana API key
- Sufficient disk space for downloaded reports

## Dependencies

See `requirements.txt` for the complete list:
- `paramiko` - SSH client
- `requests` - HTTP client
- `PyYAML` - YAML configuration parser
- `python-dateutil` - Date/time utilities
