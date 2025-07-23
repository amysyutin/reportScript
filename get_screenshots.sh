#!/bin/bash

# Grafana Screenshot Automation Wrapper
# Usage: ./get_screenshots.sh [option]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/grafana_enhanced.py"

echo "🔄 Grafana Screenshot Automation"
echo "================================="

case "${1:-download}" in
    "test")
        echo "🔍 Testing Grafana API connection..."
        python3 "$PYTHON_SCRIPT" --test-connection
        ;;
    "list")
        echo "📋 Available metrics:"
        python3 "$PYTHON_SCRIPT" --list-metrics
        ;;
    "download")
        echo "📥 Downloading all screenshots..."
        python3 "$PYTHON_SCRIPT" --download-all
        ;;
    "single")
        if [ -z "$2" ]; then
            echo "❌ Please specify metric name. Available metrics:"
            python3 "$PYTHON_SCRIPT" --list-metrics
            exit 1
        fi
        echo "🔍 Testing single metric: $2"
        python3 "$PYTHON_SCRIPT" --test-metric "$2"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  download    Download all screenshots (default)"
        echo "  test        Test Grafana API connection"
        echo "  list        List all available metrics"
        echo "  single      Test downloading a single metric"
        echo "  help        Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                    # Download all screenshots"
        echo "  $0 download           # Download all screenshots"
        echo "  $0 test               # Test connection"
        echo "  $0 list               # List metrics"
        echo "  $0 single cpu_usage   # Test single metric"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
