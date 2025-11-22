"""
Metrics collector for gathering operational data from Prometheus.
Supports data wrangling and analysis for learning purposes.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import httpx
import pandas as pd
from pathlib import Path


class PrometheusCollector:
    """Collect metrics from Prometheus for analysis."""

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)

    async def query_prometheus(self, query: str, start: datetime = None, end: datetime = None, step: str = "1m") -> Dict:
        """
        Query Prometheus using PromQL.

        Args:
            query: PromQL query string
            start: Start time for range query
            end: End time for range query
            step: Query resolution step

        Returns:
            Query results as dictionary
        """
        if start and end:
            # Range query
            params = {
                "query": query,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "step": step,
            }
            endpoint = f"{self.prometheus_url}/api/v1/query_range"
        else:
            # Instant query
            params = {"query": query}
            endpoint = f"{self.prometheus_url}/api/v1/query"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()

    async def collect_http_metrics(self, hours: int = 1) -> pd.DataFrame:
        """
        Collect HTTP request metrics.

        Args:
            hours: Number of hours to look back

        Returns:
            DataFrame with HTTP metrics
        """
        end = datetime.now()
        start = end - timedelta(hours=hours)

        queries = {
            "request_rate": 'rate(http_requests_total[5m])',
            "request_duration": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))',
            "error_rate": 'rate(http_requests_total{status=~"5.."}[5m])',
            "status_4xx": 'rate(http_requests_total{status=~"4.."}[5m])',
            "status_2xx": 'rate(http_requests_total{status=~"2.."}[5m])',
        }

        data = []
        for metric_name, query in queries.items():
            result = await self.query_prometheus(query, start, end)

            if result["status"] == "success" and result["data"]["result"]:
                for series in result["data"]["result"]:
                    for timestamp, value in series["values"]:
                        data.append({
                            "timestamp": datetime.fromtimestamp(timestamp),
                            "metric": metric_name,
                            "value": float(value),
                            **series["metric"]
                        })

        df = pd.DataFrame(data)
        return df

    async def collect_system_metrics(self, hours: int = 1) -> pd.DataFrame:
        """
        Collect system resource metrics.

        Args:
            hours: Number of hours to look back

        Returns:
            DataFrame with system metrics
        """
        end = datetime.now()
        start = end - timedelta(hours=hours)

        queries = {
            "cpu_usage": 'rate(process_cpu_seconds_total[5m])',
            "memory_usage": 'process_resident_memory_bytes',
            "open_fds": 'process_open_fds',
            "goroutines": 'go_goroutines',
        }

        data = []
        for metric_name, query in queries.items():
            result = await self.query_prometheus(query, start, end)

            if result["status"] == "success" and result["data"]["result"]:
                for series in result["data"]["result"]:
                    for timestamp, value in series["values"]:
                        data.append({
                            "timestamp": datetime.fromtimestamp(timestamp),
                            "metric": metric_name,
                            "value": float(value),
                            **series["metric"]
                        })

        df = pd.DataFrame(data)
        return df

    async def collect_business_metrics(self, hours: int = 1) -> pd.DataFrame:
        """
        Collect business-specific metrics.

        Args:
            hours: Number of hours to look back

        Returns:
            DataFrame with business metrics
        """
        end = datetime.now()
        start = end - timedelta(hours=hours)

        # These would be custom metrics exposed by the application
        queries = {
            "active_users": 'multiweb_active_users',
            "products_created": 'rate(multiweb_products_created_total[5m])',
            "transactions_completed": 'rate(multiweb_transactions_completed_total[5m])',
            "messages_sent": 'rate(multiweb_messages_sent_total[5m])',
        }

        data = []
        for metric_name, query in queries.items():
            try:
                result = await self.query_prometheus(query, start, end)

                if result["status"] == "success" and result["data"]["result"]:
                    for series in result["data"]["result"]:
                        for timestamp, value in series["values"]:
                            data.append({
                                "timestamp": datetime.fromtimestamp(timestamp),
                                "metric": metric_name,
                                "value": float(value),
                                **series["metric"]
                            })
            except Exception as e:
                print(f"Warning: Could not collect {metric_name}: {e}")

        df = pd.DataFrame(data) if data else pd.DataFrame()
        return df

    async def collect_all_metrics(self, hours: int = 1) -> Dict[str, pd.DataFrame]:
        """
        Collect all available metrics.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary of DataFrames by category
        """
        print(f"Collecting metrics for the last {hours} hour(s)...")

        http_metrics = await self.collect_http_metrics(hours)
        system_metrics = await self.collect_system_metrics(hours)
        business_metrics = await self.collect_business_metrics(hours)

        metrics = {
            "http": http_metrics,
            "system": system_metrics,
            "business": business_metrics,
        }

        # Save to files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for category, df in metrics.items():
            if not df.empty:
                filename = self.data_dir / f"{category}_metrics_{timestamp}.csv"
                df.to_csv(filename, index=False)
                print(f"Saved {category} metrics to {filename}")

                # Also save as JSON for easier parsing
                json_filename = self.data_dir / f"{category}_metrics_{timestamp}.json"
                df.to_json(json_filename, orient="records", date_format="iso")

        return metrics

    def analyze_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform basic statistical analysis on metrics.

        Args:
            df: DataFrame with metrics

        Returns:
            Dictionary with analysis results
        """
        if df.empty:
            return {}

        analysis = {
            "summary": df.describe().to_dict(),
            "total_records": len(df),
            "unique_metrics": df["metric"].nunique() if "metric" in df.columns else 0,
            "time_range": {
                "start": df["timestamp"].min().isoformat() if "timestamp" in df.columns else None,
                "end": df["timestamp"].max().isoformat() if "timestamp" in df.columns else None,
            },
        }

        # Metric-specific analysis
        if "metric" in df.columns:
            for metric in df["metric"].unique():
                metric_data = df[df["metric"] == metric]["value"]
                analysis[metric] = {
                    "mean": float(metric_data.mean()),
                    "median": float(metric_data.median()),
                    "std": float(metric_data.std()),
                    "min": float(metric_data.min()),
                    "max": float(metric_data.max()),
                    "count": int(len(metric_data)),
                }

        return analysis


async def main():
    """Main entry point for metrics collection."""
    collector = PrometheusCollector()

    # Collect metrics for the last 24 hours
    metrics = await collector.collect_all_metrics(hours=24)

    # Perform analysis
    print("\n" + "="*60)
    print("METRICS ANALYSIS")
    print("="*60)

    for category, df in metrics.items():
        if not df.empty:
            print(f"\n{category.upper()} METRICS:")
            print(f"Records: {len(df)}")

            analysis = collector.analyze_metrics(df)

            # Save analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_file = collector.data_dir / f"{category}_analysis_{timestamp}.json"
            with open(analysis_file, "w") as f:
                json.dump(analysis, f, indent=2)
            print(f"Analysis saved to {analysis_file}")

    print("\n" + "="*60)
    print("Collection completed!")
    print(f"Data directory: {collector.data_dir}")


if __name__ == "__main__":
    asyncio.run(main())
