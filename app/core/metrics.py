"""
Metrics Collection Service
Tracks performance, errors, and business metrics
"""

import structlog
from typing import Dict, Optional, List
from datetime import datetime
from collections import defaultdict
import threading

logger = structlog.get_logger()


class MetricsCollector:
    """
    Collect and expose metrics for monitoring
    
    In production, this would integrate with Prometheus/Grafana
    For now, provides in-memory metrics with JSON export
    """
    
    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._gauges: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._start_time = datetime.utcnow()
    
    def increment(self, metric_name: str, labels: Optional[Dict] = None, value: int = 1):
        """Increment a counter metric"""
        key = self._format_key(metric_name, labels)
        with self._lock:
            self._counters[key] += value
    
    def record(self, metric_name: str, value: float, labels: Optional[Dict] = None):
        """Record a histogram value (for latency, sizes, etc.)"""
        key = self._format_key(metric_name, labels)
        with self._lock:
            self._histograms[key].append(value)
            # Keep only last 1000 values to prevent memory bloat
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
    
    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict] = None):
        """Set a gauge value (for current state metrics)"""
        key = self._format_key(metric_name, labels)
        with self._lock:
            self._gauges[key] = value
    
    def _format_key(self, metric_name: str, labels: Optional[Dict]) -> str:
        """Format metric key with labels"""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{metric_name}{{{label_str}}}"
        return metric_name
    
    def get_counter(self, metric_name: str, labels: Optional[Dict] = None) -> int:
        """Get current counter value"""
        key = self._format_key(metric_name, labels)
        return self._counters.get(key, 0)
    
    def get_histogram_stats(self, metric_name: str, labels: Optional[Dict] = None) -> Dict:
        """Get histogram statistics"""
        key = self._format_key(metric_name, labels)
        values = self._histograms.get(key, [])
        
        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "sum": sum(sorted_values),
            "avg": sum(sorted_values) / count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[int(count * 0.5)],
            "p95": sorted_values[int(count * 0.95)] if count > 20 else sorted_values[-1],
            "p99": sorted_values[int(count * 0.99)] if count > 100 else sorted_values[-1]
        }
    
    def get_metrics(self) -> Dict:
        """Export all metrics in structured format"""
        with self._lock:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()
            
            histogram_stats = {}
            for key in self._histograms:
                histogram_stats[key] = self.get_histogram_stats(key)
            
            return {
                "counters": dict(self._counters),
                "histograms": histogram_stats,
                "gauges": dict(self._gauges),
                "meta": {
                    "uptime_seconds": uptime,
                    "timestamp": datetime.utcnow().isoformat(),
                    "start_time": self._start_time.isoformat()
                }
            }
    
    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format"""
        lines = []
        
        # Counters
        for key, value in self._counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")
        
        # Histogram summaries
        for key, values in self._histograms.items():
            if values:
                base_name = key.split("{")[0]
                labels = key[len(base_name):] if "{" in key else ""
                
                lines.append(f"# TYPE {base_name} histogram")
                lines.append(f"{base_name}_count{labels} {len(values)}")
                lines.append(f"{base_name}_sum{labels} {sum(values)}")
        
        # Gauges
        for key, value in self._gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")
        
        return "\n".join(lines)
    
    def reset(self):
        """Reset all metrics (useful for testing)"""
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()
            self._start_time = datetime.utcnow()


# Singleton instance
_metrics: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector singleton"""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


# Convenience functions for common metrics
def track_api_request(endpoint: str, status_code: int, duration_ms: float):
    """Track an API request"""
    metrics = get_metrics_collector()
    metrics.increment("api_requests_total", {"endpoint": endpoint, "status": str(status_code)})
    metrics.record("api_request_duration_ms", duration_ms, {"endpoint": endpoint})


def track_prediction_cycle(success: bool, duration_seconds: float, flare_class: str = None):
    """Track a prediction cycle"""
    metrics = get_metrics_collector()
    status = "success" if success else "error"
    metrics.increment("prediction_cycles_total", {"status": status})
    metrics.record("prediction_cycle_duration_seconds", duration_seconds)
    
    if flare_class:
        metrics.increment("predictions_by_class", {"class": flare_class})


def track_websocket_connection(event: str):
    """Track WebSocket connection events"""
    metrics = get_metrics_collector()
    metrics.increment("websocket_events_total", {"event": event})


def track_nasa_api_call(endpoint: str, success: bool, cached: bool = False):
    """Track NASA API calls"""
    metrics = get_metrics_collector()
    metrics.increment("nasa_api_calls_total", {
        "endpoint": endpoint,
        "success": str(success),
        "cached": str(cached)
    })
