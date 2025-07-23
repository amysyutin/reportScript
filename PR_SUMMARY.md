# PR Summary

This pull request introduces configuration validation, improved Grafana metric downloading, and time conversion utilities. Key changes include:

- `load_metrics_config` function parses `metrics_urls.yml`, ensures required fields exist, and auto-fixes misplaced `timeout` values.
- `download_grafana_metrics` downloads metrics only for enabled services, inserting service names into Grafana variables and saving into per-service folders.
- `build_grafana_url` constructs URLs with proper handling of list variables and date parameters converted to UTC ISO.
- Retries and error handling were added via a requests session with backoff, and files are saved with SSL verification.
- Tests added for config loader, Grafana URL builder, and time conversion.

## Using the script with `-grafana`

1. Configure `config.yml` with Grafana credentials, date range (`mainConfig.from`, `mainConfig.to`, `mainConfig.timezone`), and list of services in the `services` section.
2. Define metrics in `metrics_urls.yml`.
3. Run:

```bash
python3 src/main.py -grafana
```

The script reads enabled services from `config.yml`, creates `<main_folder>/metrics/<service>` for each, converts the time range to UTC, builds Grafana URLs, and downloads PNG files named `<metric>.png` or `<metric>__<service>.png`.
