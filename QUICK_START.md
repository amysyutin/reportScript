# Quick Start Guide

## TL;DR - How to use the script

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure your settings
Edit `config.yml`:
- Set your time range (`mainConfig.from` and `mainConfig.to`)
- Enable/disable services in the `services` section
- Configure SSH and Grafana credentials

### 3. Run the script
```bash
# From src/ directory
cd src
python3 main.py -grafana          # Download Grafana metrics only
python3 main.py -gatling          # Download Gatling reports only  
python3 main.py -gatling -grafana # Download both

# Or from project root
python3 src/main.py -grafana
```

### 4. Check results
- Gatling reports: `./reports/gatling/`
- Grafana metrics: `./reports/metrics/{service-name}/`
- Logs: `app.log`

## Key Configuration Files

- **`config.yml`** - Main configuration (time, services, credentials)
- **`metrics_urls.yml`** - Grafana metrics definitions (usually no changes needed)

## Alternative Methods

### Using example_usage.py for configuration
```bash
# Automatically update time range and configure services
python3 example_usage.py
```

### Using shell wrapper
```bash
# Simple shell interface
./get_screenshots.sh download     # Download all
./get_screenshots.sh test         # Test connection
./get_screenshots.sh list         # List metrics
```

### Enhanced Grafana features
```bash
# Advanced Grafana automation
python3 grafana_enhanced.py --test-connection
python3 grafana_enhanced.py --download-all
```

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- View logs in `app.log` for troubleshooting
- Run `python3 src/main.py --help` for command options
