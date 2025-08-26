#!/usr/bin/env python3
"""
Enhanced Grafana Screenshot Automation

This script provides additional features for Grafana API automation:
- Validate API connection
- Test individual metrics
- Batch download with progress
- Error recovery and retry logic
- Quality validation of downloaded images
"""

import os
import sys
import requests
import urllib3
import time
import argparse
from datetime import datetime, timedelta
import pytz
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.append('src')
from config import load_config, load_metrics_config

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GrafanaEnhanced:
    def __init__(self, config_path='config.yml'):
        """Initialize the enhanced Grafana client"""
        self.config = load_config(config_path)
        self.metrics = load_metrics_config()
        self.grafana_config = self.config['grafana']
        self.base_url = self.grafana_config['base_url']
        api_key = str(self.grafana_config['api_key'])
        if not api_key.lower().startswith('bearer '):
            api_key = f"Bearer {api_key}"
        self.headers = {'Authorization': api_key}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def test_connection(self):
        """Test Grafana API connection"""
        try:
            url = f"{self.base_url}/api/health"
            response = requests.get(url, headers=self.headers, verify=False, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("✅ Grafana API connection successful")
                return True
            else:
                self.logger.error(f"❌ Grafana API connection failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Connection error: {str(e)}")
            return False
    
    def get_dashboard_info(self, dashboard_uid):
        """Get dashboard information"""
        try:
            url = f"{self.base_url}/api/dashboards/uid/{dashboard_uid}"
            response = requests.get(url, headers=self.headers, verify=False, timeout=10)
            
            if response.status_code == 200:
                dashboard_data = response.json()
                dashboard = dashboard_data.get('dashboard', {})
                return {
                    'title': dashboard.get('title', 'Unknown'),
                    'tags': dashboard.get('tags', []),
                    'panels': len(dashboard.get('panels', []))
                }
            else:
                self.logger.warning(f"Could not get dashboard info for {dashboard_uid}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting dashboard info: {str(e)}")
            return None
    
    def build_render_url(self, metric_config):
        """Build the render URL for a metric"""
        from_time, to_time = self._get_time_range()
        
        # Build the render URL with dashboard name - this is important!
        dashboard_uid = metric_config['dashboard_uid']
        dashboard_name = metric_config['dashboard_name']
        render_url = f"{self.base_url}/render/d-solo/{dashboard_uid}/{dashboard_name}"
        
        # Format time in ISO format like in your working curl
        # Convert to UTC for the Z suffix
        from_utc = from_time.astimezone(pytz.UTC)
        to_utc = to_time.astimezone(pytz.UTC)
        from_iso = from_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        to_iso = to_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # Build parameters using the same format as your working curl
        params = {
            'orgId': str(metric_config['orgId']),
            'panelId': str(metric_config['panelId']),
            'width': str(metric_config['width']),
            'height': str(metric_config['height']),
            'timezone': self.config['mainConfig']['timezone'],  # Use 'timezone' not 'tz'
            'from': from_iso,
            'to': to_iso
        }
        
        # Add variables and replace PLACEHOLDER with actual service names
        if 'vars' in metric_config:
            for key, value in metric_config['vars'].items():
                if key != 'timeout':  # Skip timeout as it's not needed for render URL
                    if isinstance(value, list):
                        # Handle array variables
                        for item in value:
                            params[key] = item  # This will overwrite, need to handle properly
                    else:
                        # Replace PLACEHOLDER with actual service name
                        if value == "PLACEHOLDER":
                            # Get first enabled service from config
                            enabled_services = [name for name, enabled in self.config['services'].items() 
                                              if enabled and name not in ['ssh_service', 'grafana_service']]
                            if enabled_services:
                                params[key] = enabled_services[0]  # Use first enabled service
                            else:
                                params[key] = "dh-documents-service"  # fallback
                        elif isinstance(value, str) and value.startswith('$'):
                            # Don't encode $ for Grafana variables - leave as is
                            params[key] = value
                        else:
                            params[key] = value
        
        # Construct URL with parameters - minimal encoding to match curl format exactly
        param_parts = []
        for k, v in params.items():
            # Don't encode common characters that are safe in URLs
            if isinstance(v, str) and ('$__all' in v or k in ['timezone', 'from', 'to']):
                # Keep these parameters exactly as they are without encoding
                param_parts.append(f"{k}={v}")
            else:
                # Only encode if absolutely necessary
                param_parts.append(f"{k}={v}") 
        
        param_string = '&'.join(param_parts)
        return f"{render_url}?{param_string}"
    
    def _get_time_range(self):
        """Get the time range from config"""
        tz = pytz.timezone(self.config['mainConfig']['timezone'])
        
        # Try to parse with milliseconds first, then without
        from_str = self.config['mainConfig']['from']
        to_str = self.config['mainConfig']['to']
        
        try:
            from_time = datetime.strptime(from_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            from_time = datetime.strptime(from_str, "%Y-%m-%d %H:%M:%S")
            
        try:
            to_time = datetime.strptime(to_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            to_time = datetime.strptime(to_str, "%Y-%m-%d %H:%M:%S")
        
        # Localize to timezone
        from_time = tz.localize(from_time)
        to_time = tz.localize(to_time)
        
        return from_time, to_time
    
    def validate_image(self, image_path, min_size=1000):
        """Validate that the downloaded image is valid"""
        try:
            if not os.path.exists(image_path):
                return False, "File does not exist"
            
            file_size = os.path.getsize(image_path)
            if file_size < min_size:
                return False, f"File too small ({file_size} bytes)"
            
            # Check if it's a valid PNG by reading magic number
            with open(image_path, 'rb') as f:
                header = f.read(8)
                if header[:4] != b'\x89PNG':
                    return False, "Not a valid PNG file"
            
            return True, "Valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def download_metric(self, metric_config, output_dir, retries=3):
        """Download a single metric with retry logic"""
        metric_name = metric_config['name']
        
        for attempt in range(retries):
            try:
                # Build URL
                render_url = self.build_render_url(metric_config)
                self.logger.info(f"Downloading {metric_name} (attempt {attempt + 1}/{retries})")
                self.logger.info(f"URL: {render_url}")
                
                # Make request
                response = requests.get(render_url, headers=self.headers, 
                                      verify=False, timeout=120)
                response.raise_for_status()
                
                # Save file
                output_path = os.path.join(output_dir, f"{metric_name}.png")
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                # Validate image
                is_valid, message = self.validate_image(output_path)
                if is_valid:
                    self.logger.info(f"✅ {metric_name} downloaded successfully ({len(response.content)} bytes)")
                    return True, output_path
                else:
                    self.logger.warning(f"⚠️  {metric_name} validation failed: {message}")
                    if attempt < retries - 1:
                        time.sleep(2)  # Wait before retry
                        continue
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"⏱️  {metric_name} timed out (attempt {attempt + 1})")
                if attempt < retries - 1:
                    time.sleep(5)
            except Exception as e:
                self.logger.error(f"❌ {metric_name} failed: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2)
        
        return False, None
    
    def download_all_metrics(self, output_dir=None):
        """Download all metrics with progress tracking"""
        if output_dir is None:
            # Create output directory based on config
            from src.utils import create_main_folder
            main_folder = create_main_folder(self.config)
            output_dir = os.path.join(main_folder, "metrics")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        self.logger.info(f"Output directory: {output_dir}")
        
        # Track results
        successful = []
        failed = []
        
        self.logger.info(f"Starting download of {len(self.metrics)} metrics...")
        
        for i, metric in enumerate(self.metrics, 1):
            metric_name = metric['name']
            self.logger.info(f"[{i}/{len(self.metrics)}] Processing {metric_name}")
            
            # Get dashboard info
            dashboard_info = self.get_dashboard_info(metric['dashboard_uid'])
            if dashboard_info:
                self.logger.info(f"  Dashboard: {dashboard_info['title']} ({dashboard_info['panels']} panels)")
            
            # Download metric
            success, path = self.download_metric(metric, output_dir)
            
            if success:
                successful.append((metric_name, path))
            else:
                failed.append(metric_name)
        
        # Summary
        self.logger.info(f"\\n=== DOWNLOAD SUMMARY ===")
        self.logger.info(f"✅ Successful: {len(successful)}")
        self.logger.info(f"❌ Failed: {len(failed)}")
        
        if successful:
            self.logger.info("\\nSuccessful downloads:")
            for name, path in successful:
                size = os.path.getsize(path) if os.path.exists(path) else 0
                self.logger.info(f"  - {name} ({size:,} bytes)")
        
        if failed:
            self.logger.info("\\nFailed downloads:")
            for name in failed:
                self.logger.info(f"  - {name}")
        
        return len(successful), len(failed)
    
    def test_single_metric(self, metric_name):
        """Test downloading a single metric"""
        metric = next((m for m in self.metrics if m['name'] == metric_name), None)
        if not metric:
            self.logger.error(f"Metric '{metric_name}' not found in config")
            return False
        
        self.logger.info(f"Testing metric: {metric_name}")
        
        # Create temp directory
        temp_dir = "/tmp/grafana_test"
        os.makedirs(temp_dir, exist_ok=True)
        
        success, path = self.download_metric(metric, temp_dir)
        
        if success:
            self.logger.info(f"✅ Test successful! File saved to: {path}")
            self.logger.info(f"You can verify the image by opening: {path}")
        else:
            self.logger.error("❌ Test failed!")
        
        return success

def main():
    parser = argparse.ArgumentParser(description='Enhanced Grafana Screenshot Automation')
    parser.add_argument('--test-connection', action='store_true', 
                       help='Test Grafana API connection')
    parser.add_argument('--test-metric', type=str, 
                       help='Test downloading a single metric')
    parser.add_argument('--download-all', action='store_true', 
                       help='Download all metrics')
    parser.add_argument('--list-metrics', action='store_true', 
                       help='List all available metrics')
    
    args = parser.parse_args()
    
    # Initialize Grafana client
    grafana = GrafanaEnhanced()
    
    if args.test_connection:
        grafana.test_connection()
    
    elif args.list_metrics:
        print("\\nAvailable metrics:")
        for i, metric in enumerate(grafana.metrics, 1):
            print(f"{i:2d}. {metric['name']}")
            print(f"     Dashboard: {metric['dashboard_name']} (Panel: {metric['panelId']})")
    
    elif args.test_metric:
        grafana.test_single_metric(args.test_metric)
    
    elif args.download_all:
        grafana.download_all_metrics()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
