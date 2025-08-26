# Gatling Metrics Setup Guide

## Overview

This guide explains how to configure and use the new Gatling metrics functionality that downloads performance metrics from a secondary Grafana dashboard.

## Configuration Steps

### 1. Enable Gatling Metrics Service

In your `config.yml`, ensure the service is enabled:

```yaml
services:
  gatling_metrics_service: true  # Enable Gatling metrics download
```

### 2. Configure Secondary Grafana Connection

Add the Gatling Grafana configuration section to `config.yml`:

```yaml
# Configuration for Gatling metrics (secondary Grafana)
gatling_grafana:
  local_path: "./reports/metrics/gatling_metrics"
  base_url: "${GATLING_GRAFANA_BASE_URL}"
  api_key: "${GATLING_GRAFANA_API_KEY}"
  timezone: "${TIMEZONE}"
  script_name: "Attribute_Search_2"  # Change this to your test script name
  gatling_metrics_config: "gatling_metrics_urls.yml"
```

### 3. Update Script Name

Change the `script_name` parameter to match your Gatling test script:

```yaml
script_name: "Your_Test_Script_Name"  # Replace with your actual script name
```

### 4. Verify Metrics Configuration

The `gatling_metrics_urls.yml` file contains 6 pre-configured panels:
- panel_3, panel_9, panel_1, panel_6, panel_7, panel_4

These correspond to the panels from your Gatling dashboard.

## Usage

### Run with Gatling Metrics

```bash
# Download Grafana metrics (includes Gatling metrics if enabled)
python3 src/main.py -grafana

# Download both Gatling reports and all metrics
python3 src/main.py -gatling -grafana
```

### Verify Output

Check that the metrics are downloaded to:
```
reports/
└── metrics/
    └── gatling_metrics/
        ├── panel_3.png
        ├── panel_9.png
        ├── panel_1.png
        ├── panel_6.png
        ├── panel_7.png
        └── panel_4.png
```

## Customization

### Adding More Gatling Panels

To add more panels from your Gatling dashboard:

1. **Find the panel ID** from the Grafana URL (e.g., `&viewPanel=panel-5`)
2. **Add to `gatling_metrics_urls.yml`:**

```yaml
- name: "panel_5"                      # New panel
  dashboard_uid: "de9jk1ju5vmdcb"
  dashboard_name: "gatling-metrics"
  orgId: 1
  panelId: 5                           # Panel ID from URL
  width: 1000
  height: 500
  vars:
    var-DS_PROMETHEUS: "PBFA97CFB590B2093"
    var-group: "$__all"
    var-node_name: "$__all"
    var-script_name: "PLACEHOLDER"     # Will be replaced with script_name
    refresh: "5s"
    timeout: 60
```

### Changing the Script Name Dynamically

You can modify the script name for different test runs:

```yaml
# In config.yml
gatling_grafana:
  script_name: "Performance_Test_v2"  # Update for different tests
```

## Troubleshooting

### Common Issues

1. **No Gatling metrics downloaded**
   - Check that `gatling_metrics_service: true` in config.yml
   - Verify the secondary Grafana URL is accessible
   - Ensure the API key has proper permissions

2. **Wrong script name in metrics**
   - Update `script_name` in the `gatling_grafana` section
   - The script name should match exactly what appears in your Grafana dashboard

3. **Panel not found errors**
   - Verify panel IDs in `gatling_metrics_urls.yml`
   - Check that the dashboard UID is correct (`de9jk1ju5vmdcb`)

### Debugging

Enable debug logging to see detailed information:

```bash
# Check the logs for detailed error information
tail -f app.log
```

Look for lines containing "Gatling" to see the download progress and any issues.

## Technical Details

- **Dashboard UID**: `de9jk1ju5vmdcb`
- **Dashboard Name**: `gatling-metrics`
- **Variable Replacement**: `PLACEHOLDER` → `script_name` from config
- **Time Range**: Uses the same time range as other metrics from `mainConfig`
- **Output Format**: PNG images (1000x500 pixels)

## Integration with Existing Workflow

The Gatling metrics download is integrated into the existing `-grafana` flag, so:
- When you run `-grafana`, both regular service metrics AND Gatling metrics are downloaded
- Gatling metrics are stored in a separate `gatling_metrics` folder
- All use the same time range configuration
- All logging goes to the same `app.log` file
