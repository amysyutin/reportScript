import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List
import yaml

from src.utils import ensure_file_exists

logger = logging.getLogger(__name__)

@dataclass
class Metric:
    name: str
    dashboard_uid: str
    dashboard_name: str
    panelId: Any
    orgId: Any = None
    width: Any = None
    height: Any = None
    timeout: int = 60
    vars: Dict[str, Any] = field(default_factory=dict)


def load_metrics_config(path: str = "metrics_urls.yml") -> List[Metric]:
    """Load metrics configuration from YAML file with validation and autofix.

    Parameters
    ----------
    path: str
        Path to YAML configuration file.

    Returns
    -------
    List[Metric]
        Parsed metrics list as dataclasses.
    """
    ensure_file_exists(path)
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    metrics_raw = data.get("metrics", [])
    metrics: List[Metric] = []
    for idx, metric in enumerate(metrics_raw):
        # Autofix timeout under vars
        vars_section = metric.get("vars", {})
        if isinstance(vars_section, dict) and "timeout" in vars_section:
            metric.setdefault("timeout", vars_section.pop("timeout"))
            logger.warning(
                f"Autofixed timeout placement for metric {metric.get('name', idx)}"
            )
        # Validation
        for field_name in ["name", "dashboard_uid", "dashboard_name", "panelId"]:
            if field_name not in metric:
                raise ValueError(
                    f"Missing required field '{field_name}' in metric {metric.get('name', idx)}"
                )

        metrics.append(
            Metric(
                name=metric["name"],
                dashboard_uid=metric["dashboard_uid"],
                dashboard_name=metric["dashboard_name"],
                panelId=metric["panelId"],
                orgId=metric.get("orgId"),
                width=metric.get("width"),
                height=metric.get("height"),
                timeout=metric.get("timeout", 60),
                vars=metric.get("vars", {}),
            )
        )
    return metrics
