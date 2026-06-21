#!/usr/bin/env python3
import argparse
import http.client
import json
import threading
import time
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib import request


def escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def labels_to_text(labels: Dict[str, str]) -> str:
    if not labels:
        return ""
    return "{" + ",".join(f'{k}="{escape_label(str(v))}"' for k, v in sorted(labels.items())) + "}"


def metric_line(name: str, value, labels: Optional[Dict[str, str]] = None) -> str:
    return f"{name}{labels_to_text(labels or {})} {value}"


def http_get_json(url: str) -> dict:
    with request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


class MetricState:
    def __init__(self, api_base: str):
        self.api_base = api_base.rstrip("/")
        self.lock = threading.Lock()
        self.request_counts = defaultdict(int)
        self.request_duration_sum = defaultdict(float)
        self.request_duration_count = defaultdict(int)
        self.request_errors = defaultdict(int)
        self.prompt_tokens = defaultdict(int)
        self.completion_tokens = defaultdict(int)
        self.total_tokens = defaultdict(int)
        self.last_seen = {}

    def record_request(
        self,
        model: str,
        endpoint: str,
        status: int,
        duration_seconds: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        key = (model, endpoint, str(status))
        with self.lock:
            self.request_counts[key] += 1
            self.request_duration_sum[key] += duration_seconds
            self.request_duration_count[key] += 1
            if status >= 400:
                self.request_errors[key] += 1
            if prompt_tokens:
                self.prompt_tokens[model] += prompt_tokens
            if completion_tokens:
                self.completion_tokens[model] += completion_tokens
                self.total_tokens[model] += completion_tokens
            self.last_seen[key] = time.time()

    def render_metrics(self) -> str:
        with self.lock:
            lines = [
                "# HELP ollama_proxy_exporter_info Static exporter metadata.",
                "# TYPE ollama_proxy_exporter_info gauge",
                metric_line("ollama_proxy_exporter_info", 1, {"mode": "proxy+metrics"}),
                "# HELP ollama_requests_total Requests observed through the proxy.",
                "# TYPE ollama_requests_total counter",
                "# HELP ollama_request_duration_seconds_total Sum of proxy-observed request duration in seconds.",
                "# TYPE ollama_request_duration_seconds_total counter",
                "# HELP ollama_request_duration_seconds_count Count of proxy-observed requests.",
                "# TYPE ollama_request_duration_seconds_count counter",
                "# HELP ollama_request_errors_total Error responses observed through the proxy.",
                "# TYPE ollama_request_errors_total counter",
                "# HELP ollama_prompt_tokens_total Prompt tokens observed through the proxy.",
                "# TYPE ollama_prompt_tokens_total counter",
                "# HELP ollama_completion_tokens_total Completion tokens observed through the proxy.",
                "# TYPE ollama_completion_tokens_total counter",
                "# HELP ollama_tokens_generated_total Completion tokens generated through the proxy.",
                "# TYPE ollama_tokens_generated_total counter",
                "# HELP ollama_proxy_last_seen_timestamp_seconds Last time a request labelset was observed.",
                "# TYPE ollama_proxy_last_seen_timestamp_seconds gauge",
            ]

            for (model, endpoint, status), count in sorted(self.request_counts.items()):
                labels = {"model": model, "endpoint": endpoint, "status": status}
                lines.append(metric_line("ollama_requests_total", count, labels))
                lines.append(metric_line("ollama_request_duration_seconds_total", self.request_duration_sum[(model, endpoint, status)], labels))
                lines.append(metric_line("ollama_request_duration_seconds_count", self.request_duration_count[(model, endpoint, status)], labels))
                if self.request_errors[(model, endpoint, status)]:
                    lines.append(metric_line("ollama_request_errors_total", self.request_errors[(model, endpoint, status)], labels))
                lines.append(metric_line("ollama_proxy_last_seen_timestamp_seconds", self.last_seen[(model, endpoint, status)], labels))

            all_models = set(self.prompt_tokens) | set(self.completion_tokens) | set(self.total_tokens)
            for model in sorted(all_models):
                lines.append(metric_line("ollama_prompt_tokens_total", self.prompt_tokens.get(model, 0), {"model": model}))
                lines.append(metric_line("ollama_completion_tokens_total", self.completion_tokens.get(model, 0), {"model": model}))
                lines.append(metric_line("ollama_tokens_generated_total", self.total_tokens.get(model, 0), {"model": model}))

        try:
            version = http_get_json(f"{self.api_base}/api/version").get("version", "unknown")
            lines.extend([
                "# HELP ollama_proxy_backend_up Whether the backend Ollama API is reachable.",
                "# TYPE ollama_proxy_backend_up gauge",
                metric_line("ollama_proxy_backend_up", 1),
                "# HELP ollama_proxy_backend_build_info Backend Ollama version.",
                "# TYPE ollama_proxy_backend_build_info gauge",
                metric_line("ollama_proxy_backend_build_info", 1, {"version": version}),
            ])
        except Exception:
            lines.extend([
                "# HELP ollama_proxy_backend_up Whether the backend Ollama API is reachable.",
                "# TYPE ollama_proxy_backend_up gauge",
                metric_line("ollama_proxy_backend_up", 0),
            ])

        return "\n".join(lines) + "\n"


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    state: MetricState = None
    backend_host: str = "127.0.0.1"
    backend_port: int = 11434

    def do_GET(self) -> None:
        self._handle_proxy()

    def do_POST(self) -> None:
        self._handle_proxy()

    def do_PUT(self) -> None:
        self._handle_proxy()

    def do_DELETE(self) -> None:
        self._handle_proxy()

    def do_OPTIONS(self) -> None:
        self._handle_proxy()

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or "0")
        return self.rfile.read(length) if length > 0 else b""

    def _model_from_body(self, body: bytes) -> str:
        if not body:
            return "unknown"
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            return "unknown"
        return payload.get("model", "unknown")

    def _emit_metrics(self) -> None:
        payload = self.state.render_metrics().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _handle_proxy(self) -> None:
        if self.path.startswith("/metrics"):
            self._emit_metrics()
            return

        body = self._read_body()
        requested_model = self._model_from_body(body)
        started = time.time()
        conn = http.client.HTTPConnection(self.backend_host, self.backend_port, timeout=600)
        forwarded_headers = {k: v for k, v in self.headers.items() if k.lower() not in {"host", "content-length", "connection"}}
        forwarded_headers["Host"] = f"{self.backend_host}:{self.backend_port}"

        try:
            conn.request(self.command, self.path, body=body if body else None, headers=forwarded_headers)
            resp = conn.getresponse()
            content_type = resp.getheader("Content-Type", "")
            status = resp.status
            metric_model = requested_model
            prompt_tokens = 0
            completion_tokens = 0

            self.send_response(status)
            for header, value in resp.getheaders():
                if header.lower() in {"transfer-encoding", "connection", "content-length"}:
                    continue
                self.send_header(header, value)
            self.end_headers()

            if "application/x-ndjson" in content_type or self.path.startswith("/api/chat") or self.path.startswith("/api/generate"):
                raw_lines = []
                while True:
                    line = resp.readline()
                    if not line:
                        break
                    raw_lines.append(line)
                    self.wfile.write(line)
                    self.wfile.flush()
                    try:
                        event = json.loads(line.decode("utf-8"))
                    except Exception:
                        continue
                    if event.get("done"):
                        metric_model = event.get("model", metric_model)
                        prompt_tokens = int(event.get("prompt_eval_count") or 0)
                        completion_tokens = int(event.get("eval_count") or 0)
                duration = time.time() - started
                self.state.record_request(metric_model or "unknown", self.path, status, duration, prompt_tokens, completion_tokens)
                return

            payload = resp.read()
            self.wfile.write(payload)
            if payload:
                try:
                    event = json.loads(payload.decode("utf-8"))
                    metric_model = event.get("model", metric_model)
                    prompt_tokens = int(event.get("prompt_eval_count") or 0)
                    completion_tokens = int(event.get("eval_count") or 0)
                except Exception:
                    pass

            duration = time.time() - started
            self.state.record_request(metric_model or "unknown", self.path, status, duration, prompt_tokens, completion_tokens)
        except Exception:
            duration = time.time() - started
            self.state.record_request(requested_model or "unknown", self.path, 502, duration, 0, 0)
            self.send_response(502)
            self.end_headers()
            self.wfile.write(b"proxy error\n")
        finally:
            conn.close()

    def log_message(self, *_args) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Proxy Ollama API traffic and expose Prometheus metrics.")
    parser.add_argument("--listen", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=11435)
    parser.add_argument("--backend-host", default="127.0.0.1")
    parser.add_argument("--backend-port", type=int, default=11434)
    parser.add_argument("--api-base", default="http://127.0.0.1:11434")
    args = parser.parse_args()

    ProxyHandler.state = MetricState(args.api_base)
    ProxyHandler.backend_host = args.backend_host
    ProxyHandler.backend_port = args.backend_port

    server = ThreadingHTTPServer((args.listen, args.port), ProxyHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()