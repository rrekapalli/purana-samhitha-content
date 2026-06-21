#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import threading
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib import error, request


GIN_LOG_RE = re.compile(
    r'\[GIN\]\s+\S+\s+-\s+\S+\s+\|\s+(?P<status>\d+)\s+\|\s+'
    r'(?P<duration>.+?)\s+\|\s+(?P<client>.+?)\s+\|\s+'
    r'(?P<method>[A-Z]+)\s+"(?P<path>[^"]+)"'
)


def escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def prom_labels(labels: Dict[str, str]) -> str:
    if not labels:
        return ""
    rendered = ",".join(f'{key}="{escape_label(str(value))}"' for key, value in sorted(labels.items()))
    return "{" + rendered + "}"


def metric_line(name: str, value, labels: Optional[Dict[str, str]] = None) -> str:
    return f"{name}{prom_labels(labels or {})} {value}"


def http_get_json(url: str) -> dict:
    with request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def read_meminfo_bytes() -> Tuple[int, int, int]:
    meminfo = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            key, raw_value = line.split(":", 1)
            parts = raw_value.strip().split()
            if not parts:
                continue
            meminfo[key] = int(parts[0]) * 1024
    except Exception:
        return 0, 0, 0

    total = meminfo.get("MemTotal", 0)
    available = meminfo.get("MemAvailable", 0)
    used = max(total - available, 0)
    return total, available, used


def read_gpu_vram_bytes() -> List[Dict[str, object]]:
    command = [
        "nvidia-smi",
        "--query-gpu=index,name,memory.total,memory.used",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return []

    if result.returncode != 0:
        return []

    gpus = []
    for line in result.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 4:
            continue
        try:
            total_bytes = int(parts[2]) * 1024 * 1024
            used_bytes = int(parts[3]) * 1024 * 1024
        except ValueError:
            continue
        gpus.append(
            {
                "gpu": parts[0],
                "name": parts[1],
                "total_bytes": total_bytes,
                "used_bytes": used_bytes,
            }
        )
    return gpus


def parse_duration_seconds(raw: str) -> float:
    cleaned = raw.strip().replace("┬╡", "µ")
    unit_match = re.fullmatch(r"(?P<number>[0-9]+(?:\.[0-9]+)?)(?P<unit>[^0-9.]*)s", cleaned)
    if unit_match:
        number = float(unit_match.group("number"))
        unit = unit_match.group("unit")
        if unit == "":
            return number
        if unit == "m":
            return number * 60.0
        if unit == "h":
            return number * 3600.0
        if "ms" in unit:
            return number / 1000.0
        if "ns" in unit:
            return number / 1_000_000_000.0
        return number / 1_000_000.0

    composite = re.fullmatch(
        r'(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+(?:\.\d+)?)s)?',
        cleaned,
    )
    if composite:
        hours = int(composite.group("hours") or 0)
        minutes = int(composite.group("minutes") or 0)
        seconds = float(composite.group("seconds") or 0)
        return hours * 3600 + minutes * 60 + seconds

    return float(re.findall(r"[0-9]+(?:\.[0-9]+)?", cleaned)[0])


class OllamaMetricsState:
    def __init__(self, api_base: str, cursor_path: Path):
        self.api_base = api_base.rstrip("/")
        self.cursor_path = cursor_path
        self.lock = threading.Lock()
        self.cursor = self._load_cursor()
        self.request_counts = defaultdict(int)
        self.request_duration_sum = defaultdict(float)
        self.request_duration_last = {}

    def _load_cursor(self) -> Optional[str]:
        if self.cursor_path.exists():
            return self.cursor_path.read_text(encoding="utf-8").strip() or None
        return None

    def _save_cursor(self, cursor: str) -> None:
        self.cursor_path.parent.mkdir(parents=True, exist_ok=True)
        self.cursor_path.write_text(cursor, encoding="utf-8")

    def _journalctl_args(self) -> List[str]:
        args = ["journalctl", "-u", "ollama", "-o", "json", "--no-pager"]
        if self.cursor:
            args.extend(["--after-cursor", self.cursor])
        else:
            args.extend(["-n", "200"])
        return args

    def _consume_logs(self) -> None:
        result = subprocess.run(self._journalctl_args(), capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return

        latest_cursor = self.cursor
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            latest_cursor = entry.get("__CURSOR", latest_cursor)
            message = entry.get("MESSAGE", "")
            match = GIN_LOG_RE.search(message)
            if not match:
                continue

            labels = (
                match.group("method"),
                match.group("path"),
                match.group("status"),
            )
            duration = parse_duration_seconds(match.group("duration"))
            self.request_counts[labels] += 1
            self.request_duration_sum[labels] += duration
            self.request_duration_last[labels] = duration

        if latest_cursor and latest_cursor != self.cursor:
            self.cursor = latest_cursor
            self._save_cursor(latest_cursor)

    def scrape(self) -> str:
        with self.lock:
            self._consume_logs()
            lines = self._render_metrics()
            return "\n".join(lines) + "\n"

    def _render_metrics(self) -> List[str]:
        lines: List[str] = [
            "# HELP ollama_up Whether the Ollama API is reachable.",
            "# TYPE ollama_up gauge",
        ]

        api_ok = 0
        version = "unknown"
        installed_models = []
        active_models = []
        last_error = ""

        try:
            version_payload = http_get_json(f"{self.api_base}/api/version")
            tags_payload = http_get_json(f"{self.api_base}/api/tags")
            ps_payload = http_get_json(f"{self.api_base}/api/ps")
            version = version_payload.get("version", "unknown")
            installed_models = tags_payload.get("models", [])
            active_models = ps_payload.get("models", [])
            api_ok = 1
        except Exception as exc:
            last_error = str(exc)

        lines.append(metric_line("ollama_up", api_ok))
        host_memory_total, host_memory_available, host_memory_used = read_meminfo_bytes()
        gpu_vram = read_gpu_vram_bytes()
        lines.extend(
            [
                "# HELP ollama_build_info Ollama version information.",
                "# TYPE ollama_build_info gauge",
                metric_line("ollama_build_info", 1, {"version": version}),
                "# HELP ollama_active_models Number of currently loaded models.",
                "# TYPE ollama_active_models gauge",
                metric_line("ollama_active_models", len(active_models)),
                "# HELP ollama_models_installed Number of installed model entries.",
                "# TYPE ollama_models_installed gauge",
                metric_line("ollama_models_installed", len(installed_models)),
                "# HELP ollama_host_memory_total_bytes Total host RAM in bytes.",
                "# TYPE ollama_host_memory_total_bytes gauge",
                metric_line("ollama_host_memory_total_bytes", host_memory_total),
                "# HELP ollama_host_memory_available_bytes Available host RAM in bytes.",
                "# TYPE ollama_host_memory_available_bytes gauge",
                metric_line("ollama_host_memory_available_bytes", host_memory_available),
                "# HELP ollama_host_memory_used_bytes Used host RAM in bytes.",
                "# TYPE ollama_host_memory_used_bytes gauge",
                metric_line("ollama_host_memory_used_bytes", host_memory_used),
            ]
        )

        if host_memory_total > 0:
            lines.extend(
                [
                    "# HELP ollama_host_memory_used_ratio Host RAM usage ratio.",
                    "# TYPE ollama_host_memory_used_ratio gauge",
                    metric_line("ollama_host_memory_used_ratio", host_memory_used / host_memory_total),
                ]
            )

        lines.extend(
            [
                "# HELP ollama_gpu_vram_total_bytes Total GPU VRAM in bytes.",
                "# TYPE ollama_gpu_vram_total_bytes gauge",
                "# HELP ollama_gpu_vram_used_bytes Used GPU VRAM in bytes.",
                "# TYPE ollama_gpu_vram_used_bytes gauge",
                "# HELP ollama_gpu_vram_used_ratio GPU VRAM usage ratio.",
                "# TYPE ollama_gpu_vram_used_ratio gauge",
            ]
        )
        for gpu in gpu_vram:
            labels = {"gpu": str(gpu["gpu"]), "name": str(gpu["name"])}
            lines.append(metric_line("ollama_gpu_vram_total_bytes", gpu["total_bytes"], labels))
            lines.append(metric_line("ollama_gpu_vram_used_bytes", gpu["used_bytes"], labels))
            if gpu["total_bytes"]:
                lines.append(metric_line("ollama_gpu_vram_used_ratio", gpu["used_bytes"] / gpu["total_bytes"], labels))

        lines.extend(
            [
                "# HELP ollama_model_installed_info Installed model metadata.",
                "# TYPE ollama_model_installed_info gauge",
                "# HELP ollama_model_size_bytes Installed model size in bytes.",
                "# TYPE ollama_model_size_bytes gauge",
            ]
        )
        for model in installed_models:
            details = model.get("details", {})
            labels = {
                "model": model.get("name", "unknown"),
                "family": details.get("family", "unknown"),
                "quantization": details.get("quantization_level", "unknown"),
                "parameter_size": details.get("parameter_size", "unknown"),
            }
            lines.append(metric_line("ollama_model_installed_info", 1, labels))
            lines.append(metric_line("ollama_model_size_bytes", model.get("size", 0), {"model": model.get("name", "unknown")}))

        lines.extend(
            [
                "# HELP ollama_loaded_model_memory_bytes VRAM used by currently loaded models.",
                "# TYPE ollama_loaded_model_memory_bytes gauge",
                "# HELP ollama_loaded_model_size_bytes Size in bytes for currently loaded models.",
                "# TYPE ollama_loaded_model_size_bytes gauge",
            ]
        )
        for model in active_models:
            name = model.get("name", "unknown")
            lines.append(metric_line("ollama_loaded_model_memory_bytes", model.get("size_vram", 0), {"model": name}))
            lines.append(metric_line("ollama_loaded_model_size_bytes", model.get("size", 0), {"model": name}))

        lines.extend(
            [
                "# HELP ollama_http_requests_total HTTP requests observed from Ollama service logs.",
                "# TYPE ollama_http_requests_total counter",
                "# HELP ollama_http_request_duration_seconds_total Sum of observed HTTP request durations from Ollama service logs.",
                "# TYPE ollama_http_request_duration_seconds_total counter",
                "# HELP ollama_http_request_duration_seconds_last Last observed HTTP request duration from Ollama service logs.",
                "# TYPE ollama_http_request_duration_seconds_last gauge",
            ]
        )
        for labels_tuple, count in sorted(self.request_counts.items()):
            label_map = {
                "method": labels_tuple[0],
                "path": labels_tuple[1],
                "status": labels_tuple[2],
            }
            lines.append(metric_line("ollama_http_requests_total", count, label_map))
            lines.append(metric_line("ollama_http_request_duration_seconds_total", self.request_duration_sum[labels_tuple], label_map))
            lines.append(metric_line("ollama_http_request_duration_seconds_last", self.request_duration_last.get(labels_tuple, 0), label_map))

        lines.extend(
            [
                "# HELP ollama_exporter_last_scrape_success Whether the last exporter scrape from Ollama APIs succeeded.",
                "# TYPE ollama_exporter_last_scrape_success gauge",
                metric_line("ollama_exporter_last_scrape_success", api_ok),
                "# HELP ollama_exporter_info Static exporter metadata.",
                "# TYPE ollama_exporter_info gauge",
                metric_line("ollama_exporter_info", 1, {"mode": "polling+journalctl"}),
            ]
        )

        if last_error:
            lines.extend(
                [
                    "# HELP ollama_exporter_last_error Exporter scrape error state.",
                    "# TYPE ollama_exporter_last_error gauge",
                    metric_line("ollama_exporter_last_error", 1, {"message": last_error[:200]}),
                ]
            )

        return lines


class MetricsHandler(BaseHTTPRequestHandler):
    state: OllamaMetricsState = None

    def do_GET(self) -> None:
        if self.path not in ("/metrics", "/metrics/"):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found\n")
            return

        payload = self.state.scrape().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args) -> None:
        return


def main() -> None:
        parser = argparse.ArgumentParser(description="Expose Ollama monitoring metrics for Prometheus.")
        parser.add_argument("--listen", default="0.0.0.0")
        parser.add_argument("--port", type=int, default=8000)
        parser.add_argument("--api-base", default="http://127.0.0.1:11434")
        parser.add_argument("--cursor-file", default="/tmp/ollama_exporter.cursor")
        args = parser.parse_args()

        MetricsHandler.state = OllamaMetricsState(api_base=args.api_base, cursor_path=Path(args.cursor_file))
        server = ThreadingHTTPServer((args.listen, args.port), MetricsHandler)
        server.serve_forever()


if __name__ == "__main__":
    main()