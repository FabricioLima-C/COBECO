"""Small reproducible HTTP benchmark; not a substitute for concurrent load testing."""

import argparse
import json
import math
from time import perf_counter

import httpx


def run(base_url, samples):
    report = {"base_url": base_url, "samples_per_endpoint": samples, "concurrency": 1, "endpoints": {}}
    requests = [
        ("catalog", "GET", "/api/products?q=ar", None),
        (
            "comparison",
            "POST",
            "/api/compare",
            {
                "items": [{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 1}],
                "supplier_ids": list(range(1, 11)),
            },
        ),
    ]
    with httpx.Client(base_url=base_url, timeout=10) as client:
        for name, method, path, body in requests:
            durations = []
            for _ in range(samples):
                started = perf_counter()
                response = client.request(method, path, json=body)
                response.raise_for_status()
                durations.append((perf_counter() - started) * 1000)
            durations.sort()
            report["endpoints"][name] = {
                "p95_ms": round(durations[math.ceil(samples * 0.95) - 1], 2),
                "mean_ms": round(sum(durations) / samples, 2),
                "max_ms": round(max(durations), 2),
            }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--samples", type=int, default=30, choices=range(1, 41))
    args = parser.parse_args()
    print(json.dumps(run(args.url, args.samples), indent=2))
