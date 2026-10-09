"""Run a dependency-free browser smoke test for one offline trajectory viewer.

The runner speaks the small subset of the Chrome DevTools Protocol needed for
navigation, JavaScript evaluation, interaction, screenshots, and network
observation.  It intentionally implements WebSocket framing with the Python
standard library so the check does not change the project environment or
require Playwright/Selenium.

Example::

    python tools/trajectory_browser_smoke.py \
        --html runs/trace/trajectories/trial-7.html \
        --output /tmp/trajectory-browser-report.json.gz \
        --screenshot-dir /tmp/trajectory-browser-screens
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import math
import re
import socket
import struct
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from types import TracebackType
from typing import Any, Self


class CDPError(RuntimeError):
    """Raised for a failed CDP command or browser protocol exchange."""


class CDPWebSocket:
    """Minimal RFC 6455 client sufficient for a local Chromium CDP page."""

    def __init__(self, url: str, *, timeout: float = 10.0) -> None:
        self._url = url
        self._timeout = timeout
        self._socket: socket.socket | None = None
        self._counter = 0
        self.events: list[dict[str, Any]] = []

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None,
                 traceback: TracebackType | None) -> None:
        self.close()

    @staticmethod
    def _parse_url(url: str) -> tuple[str, int, str]:
        match = re.fullmatch(r"ws://([^/:]+):(\d+)(/.*)", url)
        if match is None:
            raise CDPError(f"unsupported CDP WebSocket URL: {url}")
        return match.group(1), int(match.group(2)), match.group(3)

    def connect(self) -> None:
        host, port, path = self._parse_url(self._url)
        sock = socket.create_connection((host, port), timeout=self._timeout)
        key = base64.b64encode(uuid.uuid4().bytes).decode("ascii")
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            f"Origin: http://{host}:{port}\r\n\r\n"
        ).encode("ascii")
        sock.sendall(request)
        response = self._read_until(sock, b"\r\n\r\n")
        if not response.startswith(b"HTTP/1.1 101"):
            sock.close()
            raise CDPError(f"CDP WebSocket handshake failed: {response[:200]!r}")
        self._socket = sock

    @staticmethod
    def _read_until(sock: socket.socket, marker: bytes) -> bytes:
        payload = bytearray()
        while marker not in payload:
            chunk = sock.recv(4096)
            if not chunk:
                raise CDPError("CDP WebSocket closed during handshake")
            payload.extend(chunk)
            if len(payload) > 64 * 1024:
                raise CDPError("CDP WebSocket handshake response is too large")
        return bytes(payload)

    def _send_frame(self, payload: bytes, opcode: int = 1) -> None:
        if self._socket is None:
            raise CDPError("CDP WebSocket is not connected")
        first = 0x80 | (opcode & 0x0F)
        length = len(payload)
        if length < 126:
            header = bytes((first, 0x80 | length))
        elif length <= 0xFFFF:
            header = bytes((first, 0x80 | 126)) + struct.pack(">H", length)
        else:
            header = bytes((first, 0x80 | 127)) + struct.pack(">Q", length)
        mask = uuid.uuid4().bytes[:4]
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        self._socket.sendall(header + mask + masked)

    def _recv_exact(self, size: int) -> bytes:
        if self._socket is None:
            raise CDPError("CDP WebSocket is not connected")
        result = bytearray()
        while len(result) < size:
            chunk = self._socket.recv(size - len(result))
            if not chunk:
                raise CDPError("CDP WebSocket closed unexpectedly")
            result.extend(chunk)
        return bytes(result)

    def _recv_frame(self) -> tuple[bool, int, bytes]:
        first, second = self._recv_exact(2)
        final = bool(first & 0x80)
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack(">H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self._recv_exact(8))[0]
        if length > 64 * 1024 * 1024:
            raise CDPError("CDP WebSocket frame is too large")
        mask = self._recv_exact(4) if masked else b""
        payload = self._recv_exact(length)
        if masked:
            payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        return final, opcode, payload

    def recv_message(self) -> dict[str, Any]:
        fragments: list[bytes] = []
        while True:
            final, opcode, payload = self._recv_frame()
            if opcode == 0x8:
                raise CDPError("CDP WebSocket closed by Chromium")
            if opcode == 0x9:
                self._send_frame(payload, opcode=0xA)
                continue
            if opcode != 0x1:
                continue
            fragments = [payload]
            # CDP messages normally fit in one frame.  Continue until FIN so
            # large Runtime.evaluate responses remain valid too.
            while not final:
                final, continuation_opcode, continuation = self._recv_frame()
                if continuation_opcode == 0x9:
                    self._send_frame(continuation, opcode=0xA)
                    continue
                if continuation_opcode != 0x0:
                    raise CDPError("unexpected non-continuation CDP WebSocket frame")
                fragments.append(continuation)
            try:
                return json.loads(b"".join(fragments).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CDPError("CDP WebSocket returned invalid JSON") from exc

    def command(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._socket is not None:
            self._socket.settimeout(self._timeout)
        self._counter += 1
        identifier = self._counter
        message: dict[str, Any] = {"id": identifier, "method": method}
        if params is not None:
            message["params"] = params
        self._send_frame(json.dumps(message, separators=(",", ":")).encode("utf-8"))
        while True:
            response = self.recv_message()
            if "method" in response:
                self.events.append(response)
            if response.get("id") != identifier:
                continue
            if "error" in response:
                raise CDPError(f"CDP {method} failed: {response['error']}")
            result = response.get("result", {})
            if not isinstance(result, dict):
                raise CDPError(f"CDP {method} returned a non-object result")
            return result

    def wait_for(self, method: str, timeout: float) -> dict[str, Any] | None:
        deadline = time.monotonic() + timeout
        for event in self.events:
            if event.get("method") == method:
                return event
        while time.monotonic() < deadline:
            if self._socket is None:
                raise CDPError("CDP WebSocket is not connected")
            remaining = max(0.05, deadline - time.monotonic())
            self._socket.settimeout(remaining)
            try:
                event = self.recv_message()
            except TimeoutError:
                return None
            if "method" in event:
                self.events.append(event)
            if event.get("method") == method:
                return event
        return None

    def evaluate(self, expression: str, *, await_promise: bool = False) -> Any:
        result = self.command(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise,
            },
        )
        if "exceptionDetails" in result:
            raise CDPError(f"JavaScript evaluation failed: {result['exceptionDetails']}")
        remote = result.get("result", {})
        if not isinstance(remote, dict):
            raise CDPError("JavaScript returned an invalid result")
        if "value" in remote:
            return remote["value"]
        if "unserializableValue" in remote:
            return remote["unserializableValue"]
        return None

    def close(self) -> None:
        if self._socket is None:
            return
        try:
            self._send_frame(b"", opcode=0x8)
        except (OSError, CDPError):
            pass
        try:
            self._socket.close()
        finally:
            self._socket = None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _json_endpoint(port: int, endpoint: str, timeout: float) -> Any:
    url = f"http://127.0.0.1:{port}{endpoint}"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _wait_for_page(port: int, timeout: float) -> tuple[dict[str, Any], dict[str, Any]]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            version = _json_endpoint(port, "/json/version", min(1.0, timeout))
            pages = _json_endpoint(port, "/json/list", min(1.0, timeout))
            page = next(
                item for item in pages
                if item.get("type") == "page" and item.get("url") == "about:blank"
            )
            return version, page
        except (OSError, StopIteration, ValueError, urllib.error.URLError) as exc:
            last_error = exc
            time.sleep(0.05)
    raise CDPError(f"Chromium did not expose a CDP page: {last_error}")


def _decode_embedded_arrays(document: str) -> tuple[dict[str, Any], dict[str, Any]]:
    match = re.search(
        r'<script id="trajectory-data" type="application/json">(.*?)</script>',
        document,
        re.DOTALL,
    )
    if match is None:
        raise ValueError("trajectory HTML has no embedded trajectory-data block")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict) or not isinstance(payload.get("arrays"), dict):
        raise TypeError("embedded trajectory payload has an invalid shape")

    arrays: dict[str, Any] = {}
    for name, spec in payload["arrays"].items():
        if not isinstance(spec, dict) or not isinstance(spec.get("base64"), str):
            raise TypeError(f"embedded array {name!r} is malformed")
        shape = spec.get("shape")
        if not isinstance(shape, list) or not all(isinstance(item, int) and item >= 0 for item in shape):
            raise TypeError(f"embedded array {name!r} has an invalid shape")
        raw = base64.b64decode(spec["base64"], validate=True)
        dtype = spec.get("dtype")
        item_size = {"<f4": 4, "<i4": 4, "<i8": 8, "|u1": 1, "u1": 1}.get(dtype)
        if item_size is None:
            raise ValueError(f"embedded array {name!r} has unsupported dtype {dtype!r}")
        count = math.prod(shape)
        if len(raw) != count * item_size:
            raise ValueError(f"embedded array {name!r} byte length does not match shape")
        if dtype == "<f4":
            values = [item[0] for item in struct.iter_unpack("<f", raw)]
        elif dtype == "<i4":
            values = [item[0] for item in struct.iter_unpack("<i", raw)]
        elif dtype == "<i8":
            values = [item[0] for item in struct.iter_unpack("<q", raw)]
        else:
            values = list(raw)
        arrays[name] = {"shape": shape, "dtype": dtype, "values": values}
    return arrays, payload.get("metadata", {})


def _flat_value(arrays: dict[str, Any], name: str, index: int) -> Any:
    values = arrays[name]["values"]
    try:
        return values[index]
    except IndexError as exc:
        raise ValueError(f"embedded array {name!r} is too short") from exc


def _expected_polygon(arrays: dict[str, Any], frame: int, square: int = 0) -> list[tuple[float, float]]:
    shape = arrays["poses"]["shape"]
    if len(shape) != 3 or shape[2] != 3:
        raise ValueError("embedded poses must have shape [F, N, 3]")
    frames, squares = shape[:2]
    if not 0 <= frame < frames or not 0 <= square < squares:
        raise ValueError("selected frame or square is outside embedded poses")
    initial_side = float(_flat_value(arrays, "side", 0))
    if not math.isfinite(initial_side) or initial_side <= 0:
        raise ValueError("initial side is not positive and finite")
    scale = min(900.0 - 2.0 * 70.0, 700.0 - 2.0 * 70.0) / initial_side
    offset = (frame * squares + square) * 3
    x, y, theta = (float(arrays["poses"]["values"][offset + i]) for i in range(3))
    cosine = math.cos(theta)
    sine = math.sin(theta)
    ux, uy = cosine, sine
    vx, vy = -sine, cosine
    points = []
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        world_x = x + 0.5 * (sx * ux + sy * vx)
        world_y = y + 0.5 * (sx * uy + sy * vy)
        points.append((450.0 + world_x * scale, 350.0 - world_y * scale))
    return points


def _parse_svg_polygon(svg: str) -> list[tuple[float, float]]:
    match = re.search(r'<polygon\s+points="([^"]+)"', svg)
    if match is None:
        raise ValueError("exported SVG has no polygon")
    points: list[tuple[float, float]] = []
    for token in match.group(1).split():
        x_text, separator, y_text = token.partition(",")
        if not separator:
            raise ValueError(f"malformed SVG point {token!r}")
        points.append((float(x_text), float(y_text)))
    return points


def _close_points(actual: list[tuple[float, float]], expected: list[tuple[float, float]], tolerance: float = 1e-4) -> bool:
    return len(actual) == len(expected) and all(
        math.isclose(ax, ex, rel_tol=tolerance, abs_tol=tolerance)
        and math.isclose(ay, ey, rel_tol=tolerance, abs_tol=tolerance)
        for (ax, ay), (ex, ey) in zip(actual, expected)
    )


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0, compresslevel=3) as compressed:
                compressed.write(encoded)
            raw.flush()
            import os

            os.fsync(raw.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _start_chromium(profile: Path, port: int) -> subprocess.Popen[bytes]:
    command = [
        "/usr/bin/chromium",
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-crashpad",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-sync",
        "--metrics-recording-only",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile}",
        f"--remote-debugging-port={port}",
        "about:blank",
    ]
    return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_smoke(html_path: Path, output: Path, screenshot_directory: Path, timeout: float) -> dict[str, Any]:
    """Run the browser check and return the report mapping."""

    if not html_path.is_file():
        raise FileNotFoundError(html_path)
    source = html_path.read_text(encoding="utf-8")
    arrays, metadata = _decode_embedded_arrays(source)
    pose_shape = arrays.get("poses", {}).get("shape", [])
    if len(pose_shape) != 3 or not pose_shape[0]:
        raise ValueError("viewer must contain at least one recorded frame")
    frame_count = int(pose_shape[0])
    selected_frame = 1 if frame_count >= 3 else 0
    expected_points = _expected_polygon(arrays, selected_frame)

    screenshot_directory.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_directory / "trajectory-viewer.png"
    report: dict[str, Any] = {
        "status": "FAIL",
        "html": str(html_path),
        "html_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "selected_frame": selected_frame,
        "frame_count": frame_count,
        "trial_id": metadata.get("trial_id") if isinstance(metadata, dict) else None,
        "viewport": {"width": 1500, "height": 1000, "device_scale_factor": 1},
        "screenshot": str(screenshot_path),
        "network_urls": [],
        "non_file_network_urls": [],
        "page_errors": [],
    }
    browser: subprocess.Popen[str] | None = None
    try:
        port = _free_port()
        with tempfile.TemporaryDirectory(prefix="asquerix-browser-smoke-", dir="/tmp") as profile_text:
            profile = Path(profile_text)
            browser = _start_chromium(profile, port)
            version, page = _wait_for_page(port, timeout)
            report["browser"] = {
                "product": version.get("Browser"),
                "protocol": version.get("Protocol-Version"),
                "executable": "/usr/bin/chromium",
            }
            page_url = page.get("webSocketDebuggerUrl")
            if not isinstance(page_url, str):
                raise CDPError("Chromium page has no WebSocket debugger URL")
            with CDPWebSocket(page_url, timeout=timeout) as cdp:
                cdp.command("Runtime.enable")
                cdp.command("Page.enable")
                cdp.command("Network.enable")
                cdp.command(
                    "Emulation.setDeviceMetricsOverride",
                    {"width": 1500, "height": 1000, "deviceScaleFactor": 1, "mobile": False},
                )
                cdp.command("Page.navigate", {"url": html_path.resolve().as_uri()})
                if cdp.wait_for("Page.loadEventFired", timeout) is None:
                    raise CDPError("viewer did not fire Page.loadEventFired")
                time.sleep(0.15)

                def evaluate(expression: str, *, await_promise: bool = False) -> Any:
                    return cdp.evaluate(expression, await_promise=await_promise)

                initial = evaluate(
                    "({frame:document.getElementById('frame-output').textContent, "
                    "play:document.getElementById('play-pause').textContent, "
                    "slider:document.getElementById('frame-slider').value, "
                    "canvas:!!document.getElementById('initial-canvas').getContext('2d')})"
                )
                if not isinstance(initial, dict):
                    raise CDPError("viewer initial state is not an object")
                if initial.get("frame") != f"Frame 1 / {frame_count}" or initial.get("play") != "Play":
                    raise CDPError(f"viewer did not start paused at frame 1: {initial}")
                if not initial.get("canvas"):
                    raise CDPError("viewer initial canvas did not initialize")

                cdp.command("Runtime.evaluate", {"expression": "document.getElementById('next-frame').click()"})
                after_next = evaluate(
                    "({frame:document.getElementById('frame-output').textContent, "
                    "slider:document.getElementById('frame-slider').value})"
                )
                expected_next = min(1, frame_count - 1)
                if not isinstance(after_next, dict) or after_next.get("slider") != str(expected_next):
                    raise CDPError(f"next-frame control selected an unexpected frame: {after_next}")

                cdp.command(
                    "Runtime.evaluate",
                    {
                        "expression": (
                            "const slider=document.getElementById('frame-slider'); "
                            f"slider.value='{selected_frame}'; "
                            "slider.dispatchEvent(new Event('input', {bubbles:true}));"
                        )
                    },
                )
                selected_state = evaluate(
                    "({frame:document.getElementById('frame-output').textContent, "
                    "slider:document.getElementById('frame-slider').value})"
                )
                if not isinstance(selected_state, dict) or selected_state.get("slider") != str(selected_frame):
                    raise CDPError(f"slider selected an unexpected frame: {selected_state}")

                cdp.command("Runtime.evaluate", {"expression": "document.getElementById('first-frame').click(); const speed=document.getElementById('speed'); speed.value='16'; speed.dispatchEvent(new Event('change')); document.getElementById('play-pause').click();"})
                time.sleep(min(0.7, max(0.12, (frame_count + 1) / 32.0)))
                playing_state = evaluate(
                    "({frame:document.getElementById('frame-slider').value, "
                    "button:document.getElementById('play-pause').textContent})"
                )
                if isinstance(playing_state, dict) and playing_state.get("button") == "Pause":
                    cdp.command("Runtime.evaluate", {"expression": "document.getElementById('play-pause').click()"})
                if frame_count > 1 and (not isinstance(playing_state, dict) or playing_state.get("frame") == "0"):
                    raise CDPError(f"playback did not advance a frame: {playing_state}")

                cdp.command(
                    "Runtime.evaluate",
                    {
                        "expression": (
                            "window.__asquerixSmokeBlob=null; "
                            "window.__asquerixSmokeOldCreate=URL.createObjectURL; "
                            "URL.createObjectURL=(blob)=>{window.__asquerixSmokeBlob=blob; return window.__asquerixSmokeOldCreate(blob)}; "
                            f"document.getElementById('frame-slider').value='{selected_frame}'; "
                            "document.getElementById('frame-slider').dispatchEvent(new Event('input', {bubbles:true})); "
                            "document.getElementById('export-svg').click();"
                        )
                    },
                )
                time.sleep(0.1)
                exported_svg = evaluate(
                    "window.__asquerixSmokeBlob ? new Response(window.__asquerixSmokeBlob).text() : ''",
                    await_promise=True,
                )
                if not isinstance(exported_svg, str) or not exported_svg.startswith("<svg"):
                    raise CDPError("export-current-frame did not produce SVG data")
                actual_points = _parse_svg_polygon(exported_svg)
                if not _close_points(actual_points, expected_points):
                    raise CDPError(
                        f"SVG polygon does not match selected frame {selected_frame}: "
                        f"actual={actual_points!r}, expected={expected_points!r}"
                    )
                if f"frame {selected_frame + 1}" not in exported_svg:
                    raise CDPError("SVG export title does not identify the selected frame")
                report["controls"] = {
                    "initial": initial,
                    "after_next": after_next,
                    "selected": selected_state,
                    "after_play": playing_state,
                    "paused_after_play": evaluate("document.getElementById('play-pause').textContent"),
                }
                report["svg_export"] = {
                    "bytes": len(exported_svg.encode("utf-8")),
                    "frame": selected_frame,
                    "polygon_matches_selected_coordinates": True,
                    "polygon_points": actual_points,
                    "expected_points": expected_points,
                    "sha256": hashlib.sha256(exported_svg.encode("utf-8")).hexdigest(),
                }
                screenshot = cdp.command("Page.captureScreenshot", {"format": "png", "fromSurface": True})
                screenshot_data = screenshot.get("data")
                if not isinstance(screenshot_data, str):
                    raise CDPError("Page.captureScreenshot returned no PNG data")
                screenshot_bytes = base64.b64decode(screenshot_data, validate=True)
                if screenshot_bytes[:8] != b"\x89PNG\r\n\x1a\n" or len(screenshot_bytes) < 24:
                    raise CDPError("Page.captureScreenshot returned invalid PNG data")
                screenshot_width, screenshot_height = struct.unpack(">II", screenshot_bytes[16:24])
                if (screenshot_width, screenshot_height) != (1500, 1000):
                    raise CDPError(
                        f"screenshot dimensions are {screenshot_width}x{screenshot_height}, expected 1500x1000"
                    )
                screenshot_path.write_bytes(screenshot_bytes)
                report["screenshot_dimensions"] = {
                    "width": screenshot_width,
                    "height": screenshot_height,
                }

                report["network_urls"] = [
                    event.get("params", {}).get("request", {}).get("url")
                    for event in cdp.events
                    if event.get("method") == "Network.requestWillBeSent"
                ]
                report["network_urls"] = [url for url in report["network_urls"] if isinstance(url, str)]
                report["non_file_network_urls"] = [
                    url for url in report["network_urls"]
                    if not url.startswith("file://")
                ]
                report["page_errors"] = [
                    event.get("params", {})
                    for event in cdp.events
                    if event.get("method") in {"Runtime.exceptionThrown", "Log.entryAdded"}
                    and (
                        event.get("method") == "Runtime.exceptionThrown"
                        or event.get("params", {}).get("entry", {}).get("level") == "error"
                    )
                ]
                if report["non_file_network_urls"]:
                    raise CDPError(f"viewer made non-file network requests: {report['non_file_network_urls']}")
                if report["page_errors"]:
                    raise CDPError(f"viewer emitted page errors: {report['page_errors']}")
                report["status"] = "PASS"
    finally:
        if browser is not None and browser.poll() is None:
            browser.terminate()
            try:
                browser.wait(timeout=3)
            except subprocess.TimeoutExpired:
                browser.kill()
                browser.wait(timeout=3)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, required=True, help="Self-contained trajectory HTML file")
    parser.add_argument("--output", type=Path, required=True, help="Gzip JSON report path")
    parser.add_argument(
        "--screenshot-dir",
        type=Path,
        default=None,
        help="Directory for the 1500x1000 PNG screenshot (default: report sibling screenshots)",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="Browser/CDP timeout in seconds")
    args = parser.parse_args(argv)
    screenshot_directory = args.screenshot_dir or args.output.parent / "trajectory-browser-screens"
    report: dict[str, Any]
    try:
        report = run_smoke(args.html, args.output, screenshot_directory, args.timeout)
    except Exception as exc:  # noqa: BLE001 - the CLI must persist a failure report
        report = {
            "status": "FAIL",
            "html": str(args.html),
            "error": f"{type(exc).__name__}: {exc}",
            "screenshot": None,
        }
    _write_report(args.output, report)
    print(json.dumps({"status": report["status"], "report": str(args.output), "screenshot": report.get("screenshot")}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
