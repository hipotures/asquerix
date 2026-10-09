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
import xml.etree.ElementTree as ET
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


def _expected_polygon(arrays: dict[str, Any], frame: int, square: int = 0, zoom: float = 1, center: tuple[float, float] = (0, 0)) -> list[tuple[float, float]]:
    shape = arrays["poses"]["shape"]
    if len(shape) != 3 or shape[2] != 3:
        raise ValueError("embedded poses must have shape [F, N, 3]")
    frames, squares = shape[:2]
    if not 0 <= frame < frames or not 0 <= square < squares:
        raise ValueError("selected frame or square is outside embedded poses")
    initial_side = float(_flat_value(arrays, "side", 0))
    if not math.isfinite(initial_side) or initial_side <= 0:
        raise ValueError("initial side is not positive and finite")
    scale = min(900.0 - 2.0 * 70.0, 700.0 - 2.0 * 70.0) / initial_side * zoom
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
        points.append((450.0 + (world_x - center[0]) * scale, 350.0 - (world_y - center[1]) * scale))
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
        math.isclose(ax, ex, rel_tol=1e-12, abs_tol=tolerance)
        and math.isclose(ay, ey, rel_tol=1e-12, abs_tol=tolerance)
        for (ax, ay), (ex, ey) in zip(actual, expected)
    )


def _check_center_trails(svg: str, arrays: dict[str, Any], frame: int, squares: list[int]) -> None:
    root = ET.fromstring(svg)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    groups = root.findall(".//svg:g[@data-center-trail]", namespace)
    ids = arrays["square_ids"]["values"]
    if [group.attrib["data-center-trail"] for group in groups] != [str(ids[square]) for square in squares]:
        raise CDPError("SVG center trails do not respect the selected square(s)")
    square_count = arrays["poses"]["shape"][1]
    scale = 560.0 / float(_flat_value(arrays, "side", 0)) * float(root.attrib["data-zoom"])
    center = float(root.attrib["data-view-x"]), float(root.attrib["data-view-y"])
    first_frame = int(root.attrib["data-trail-start"])
    for square, group in zip(squares, groups):
        expected_segments = []
        segment = []
        for saved in range(first_frame, frame + 1):
            offset = (saved * square_count + square) * 3
            x, y = arrays["poses"]["values"][offset:offset + 2]
            if math.isfinite(x) and math.isfinite(y):
                segment.append((450.0 + (x - center[0]) * scale, 350.0 - (y - center[1]) * scale))
            elif segment:
                expected_segments.append(segment)
                segment = []
        if segment:
            expected_segments.append(segment)
        lines = group.findall("svg:polyline", namespace)
        if len(lines) != len(expected_segments):
            raise CDPError("SVG center trail joined a non-finite gap or omitted a segment")
        for line, expected in zip(lines, expected_segments):
            actual = [tuple(map(float, token.split(","))) for token in line.attrib["points"].split()]
            if not _close_points(actual, expected):
                raise CDPError("SVG center trail is not the retained center sequence through the selected frame")


def _check_label_clearance(svg: str) -> None:
    root = ET.fromstring(svg)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    labels = {item.attrib["data-label"]: item for item in root.findall("svg:rect[@data-label]", namespace)}
    for marker in root.findall("svg:line[@data-orientation]", namespace):
        label = labels[marker.attrib["data-orientation"]]
        left, top, width, height = (float(label.attrib[name]) for name in ("x", "y", "width", "height"))
        x1, y1, x2, y2 = (float(marker.attrib[name]) for name in ("x1", "y1", "x2", "y2"))
        for sample in range(51):
            x = x1 + (x2 - x1) * sample / 50
            y = y1 + (y2 - y1) * sample / 50
            if left - 1 <= x <= left + width + 1 and top - 1 <= y <= top + height + 1:
                raise CDPError("SVG orientation mark intersects its square ID label")


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
    selected_frame = frame_count // 2
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
                caption_above_canvas = evaluate("document.getElementById('initial-caption').getBoundingClientRect().bottom <= document.getElementById('initial-canvas').getBoundingClientRect().top && document.getElementById('initial-caption').textContent.startsWith('L = ')")
                if not caption_above_canvas:
                    raise CDPError("initial container side caption is not outside the drawing")
                validation_detail = evaluate("document.getElementById('validation-detail').textContent")
                if not isinstance(validation_detail, str) or "validator_version" in validation_detail or "{\"" in validation_detail:
                    raise CDPError("viewer exposes raw validation JSON instead of readable measurements")

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
                square_count = int(pose_shape[1])
                _check_center_trails(exported_svg, arrays, selected_frame, list(range(square_count)))
                _check_label_clearance(exported_svg)
                legend_values = evaluate("[...document.querySelectorAll('#square-legend button')].map(key=>({id:key.textContent,color:key.style.getPropertyValue('--square-color')}))")
                if not isinstance(legend_values, list) or [entry["id"] for entry in legend_values] != [str(square_id) for square_id in arrays["square_ids"]["values"]]:
                    raise CDPError("square legend IDs do not match the recorded square ordering")
                if len({entry["color"] for entry in legend_values}) != square_count:
                    raise CDPError("square legend repeats a color for different IDs")
                polygons = ET.fromstring(exported_svg).findall("{http://www.w3.org/2000/svg}polygon")
                finite_square_indices = [square for square in range(square_count) if all(math.isfinite(value) for value in arrays["poses"]["values"][(selected_frame * square_count + square) * 3:(selected_frame * square_count + square + 1) * 3])]
                if [polygon.attrib["stroke"] for polygon in polygons] != [legend_values[square]["color"] for square in finite_square_indices]:
                    raise CDPError("legend colors do not match the selected square polygons")

                def capture_svg() -> str:
                    evaluate("document.getElementById('export-svg').click()")
                    result = evaluate("new Response(window.__asquerixSmokeBlob).text()", await_promise=True)
                    if not isinstance(result, str):
                        raise CDPError("SVG export did not return text")
                    return result

                evaluate("window.__initialBeforeTrails=document.getElementById('initial-canvas').toDataURL(); window.__currentBeforeTrails=document.getElementById('current-canvas').toDataURL(); document.getElementById('show-trails').click()")
                trails_hidden = evaluate("({disabled:document.getElementById('trail-square').disabled, initialUnchanged:window.__initialBeforeTrails===document.getElementById('initial-canvas').toDataURL(), currentChanged:window.__currentBeforeTrails!==document.getElementById('current-canvas').toDataURL()})")
                if not isinstance(trails_hidden, dict) or not trails_hidden.get("disabled") or not trails_hidden.get("initialUnchanged"):
                    raise CDPError("center trail toggle changed the initial reference or did not disable selection")
                panel_size = evaluate("['initial-canvas','current-canvas'].map(id=>{const r=document.getElementById(id).getBoundingClientRect();return [r.width,r.height]})")
                initial_side = float(_flat_value(arrays, "side", 0))
                canvas_scale = max(1.0, min((value - 28) / initial_side for panel in panel_size for value in panel))
                visible_motion = False
                for square in range(square_count):
                    current_offset = (selected_frame * square_count + square) * 3
                    x, y = arrays["poses"]["values"][current_offset:current_offset + 2]
                    for saved in range(selected_frame):
                        offset = (saved * square_count + square) * 3
                        old_x, old_y = arrays["poses"]["values"][offset:offset + 2]
                        if math.hypot(x - old_x, y - old_y) * canvas_scale > len(str(arrays["square_ids"]["values"][square])) * 8 + 20:
                            visible_motion = True
                if visible_motion and not trails_hidden.get("currentChanged"):
                    raise CDPError("center trail toggle did not change Canvas pixels for visible center motion")
                _check_center_trails(capture_svg(), arrays, selected_frame, [])
                evaluate("document.querySelector('#square-legend button[data-square-index=\"0\"]').click()")
                selected_legend = evaluate("document.getElementById('show-trails').checked && !document.getElementById('trail-square').disabled && document.getElementById('trail-square').value==='0' && document.querySelector('#square-legend button[data-square-index=\"0\"]').getAttribute('aria-pressed')==='true'")
                if not selected_legend:
                    raise CDPError("legend click did not enable and select its square trail")
                focused_svg = capture_svg()
                _check_center_trails(focused_svg, arrays, selected_frame, list(range(square_count)))
                focused_groups = ET.fromstring(focused_svg).findall("{http://www.w3.org/2000/svg}g")
                if float(focused_groups[0].attrib['opacity']) <= max((float(group.attrib['opacity']) for group in focused_groups[1:]), default=0):
                    raise CDPError("focusing an ID did not dim other center trails")
                evaluate("document.getElementById('only-selected-trail').click()")
                _check_center_trails(capture_svg(), arrays, selected_frame, [0])
                next_square = min(1, square_count - 1)
                evaluate(f"document.getElementById('trail-square').value='{next_square}'; document.getElementById('trail-square').dispatchEvent(new Event('change'))")
                _check_center_trails(capture_svg(), arrays, selected_frame, [next_square])
                evaluate("window.__withSquares=document.getElementById('current-canvas').toDataURL(); document.getElementById('show-squares').click()")
                no_squares_svg = capture_svg()
                if "<polygon" in no_squares_svg or not evaluate("window.__withSquares!==document.getElementById('current-canvas').toDataURL()"):
                    raise CDPError("square visibility toggle did not hide square geometry in Canvas and SVG")
                _check_center_trails(no_squares_svg, arrays, selected_frame, [next_square])
                evaluate("document.getElementById('show-squares').click()")
                evaluate("document.getElementById('show-ids').click(); document.getElementById('show-orientation').click()")
                hidden_svg = capture_svg()
                if "data-label=" in hidden_svg or "data-orientation=" in hidden_svg:
                    raise CDPError("SVG export ignored ID or orientation visibility toggles")
                evaluate("document.getElementById('show-ids').click(); document.getElementById('show-orientation').click(); document.getElementById('only-selected-trail').click(); document.getElementById('trail-square').value='all'; document.getElementById('trail-square').dispatchEvent(new Event('change'))")
                evaluate("document.getElementById('trail-history').value='3'; document.getElementById('trail-history').dispatchEvent(new Event('change'))")
                short_svg = capture_svg()
                if int(ET.fromstring(short_svg).attrib['data-trail-start']) != max(0, selected_frame - 2):
                    raise CDPError("short trail window does not retain the last K saved frames")
                _check_center_trails(short_svg, arrays, selected_frame, list(range(square_count)))
                evaluate("document.getElementById('trail-history').value='0'; document.getElementById('trail-history').dispatchEvent(new Event('change')); document.getElementById('show-container').click()")
                if "data-container-boundary=" in capture_svg():
                    raise CDPError("container visibility toggle left a boundary in SVG")
                evaluate("document.getElementById('show-container').click(); window.__initialBeforeZoom=document.getElementById('initial-canvas').toDataURL(); document.getElementById('zoom-in').click()")
                zoom_svg = capture_svg()
                if float(ET.fromstring(zoom_svg).attrib['data-zoom']) != 2 or not _close_points(_parse_svg_polygon(zoom_svg), _expected_polygon(arrays, selected_frame, zoom=2)):
                    raise CDPError("zoom did not use the same physical transform for the squares")
                _check_center_trails(zoom_svg, arrays, selected_frame, list(range(square_count)))
                if not evaluate("window.__initialBeforeZoom===document.getElementById('initial-canvas').toDataURL()"):
                    raise CDPError("current-panel zoom changed the initial reference")

                def drag_mouse(start: tuple[float, float], end: tuple[float, float]) -> None:
                    cdp.command("Input.dispatchMouseEvent", {"type": "mousePressed", "x": start[0], "y": start[1], "button": "left", "buttons": 1, "clickCount": 1})
                    cdp.command("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": end[0], "y": end[1], "button": "left", "buttons": 1})
                    cdp.command("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": end[0], "y": end[1], "button": "left", "buttons": 0, "clickCount": 1})

                evaluate("document.getElementById('current-canvas').scrollIntoView({block:'center'})")
                scene_rect = evaluate("(()=>{const r=document.getElementById('current-canvas').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()")
                drag_mouse((scene_rect['x'], scene_rect['y']), (scene_rect['x'] + 40, scene_rect['y'] + 20))
                panned_svg = capture_svg()
                panned_root = ET.fromstring(panned_svg)
                panned_center = float(panned_root.attrib['data-view-x']), float(panned_root.attrib['data-view-y'])
                if panned_center == (0, 0) or not _close_points(_parse_svg_polygon(panned_svg), _expected_polygon(arrays, selected_frame, zoom=2, center=panned_center)):
                    raise CDPError("drag panning did not preserve the shared world transform")
                _check_center_trails(panned_svg, arrays, selected_frame, list(range(square_count)))
                cdp.command("Input.dispatchMouseEvent", {"type": "mouseWheel", "x": scene_rect['x'], "y": scene_rect['y'], "deltaX": 0, "deltaY": -100})
                time.sleep(0.1)
                if float(ET.fromstring(capture_svg()).attrib['data-zoom']) <= 2:
                    raise CDPError("mouse wheel did not zoom the current scene")
                evaluate("document.getElementById('reset-view').click(); document.getElementById('fit-current').click()")
                fit_root = ET.fromstring(capture_svg())
                expected_fit = max(0.25, min(65536, float(_flat_value(arrays, 'side', 0)) / float(_flat_value(arrays, 'side', selected_frame))))
                if not math.isclose(float(fit_root.attrib['data-zoom']), expected_fit, rel_tol=1e-6):
                    raise CDPError("fit-container did not use the selected frame side")
                evaluate("document.getElementById('fit-trajectory').click(); document.getElementById('reset-view').click(); document.querySelector('#square-legend button[data-square-index=\"0\"]').click(); document.getElementById('current-zoom').value='4096'; document.getElementById('current-zoom').dispatchEvent(new Event('change')); document.getElementById('focus-trail').click()")
                micro_root = ET.fromstring(capture_svg())
                current_offset = selected_frame * square_count * 3
                expected_center = tuple(arrays['poses']['values'][current_offset:current_offset + 2])
                if float(micro_root.attrib['data-zoom']) != 4096 or (float(micro_root.attrib['data-view-x']), float(micro_root.attrib['data-view-y'])) != expected_center:
                    raise CDPError("micromovement zoom did not center on the selected recorded pose")
                evaluate("document.getElementById('current-zoom').value='65536'; document.getElementById('current-zoom').dispatchEvent(new Event('change'))")
                maximum_svg = capture_svg()
                if float(ET.fromstring(maximum_svg).attrib['data-zoom']) != 65536 or not _close_points(_parse_svg_polygon(maximum_svg), _expected_polygon(arrays, selected_frame, zoom=65536, center=expected_center)):
                    raise CDPError("maximum micromovement zoom changed the recorded geometry transform")
                evaluate("document.getElementById('current-zoom').value='4096'; document.getElementById('current-zoom').dispatchEvent(new Event('change'))")
                if selected_frame + 1 < frame_count:
                    evaluate("document.getElementById('next-frame').click()")
                    advanced_root = ET.fromstring(capture_svg())
                    if any(advanced_root.attrib[key] != micro_root.attrib[key] for key in ('data-zoom', 'data-view-x', 'data-view-y')):
                        raise CDPError("changing frames moved the camera automatically")
                evaluate("document.getElementById('reset-view').click(); document.getElementById('first-frame').click(); document.getElementById('current-canvas').scrollIntoView({block:'center'})")
                canvas_rects = evaluate("['initial-canvas','current-canvas'].map(id=>{const r=document.getElementById(id).getBoundingClientRect();return {left:r.left,top:r.top,width:r.width,height:r.height}})")
                click_scale = max(1.0, min((math.floor(panel[key]) - 28) / initial_side for panel in canvas_rects for key in ('width','height')))
                target_x, target_y = arrays['poses']['values'][(square_count - 1) * 3:(square_count - 1) * 3 + 2]
                current_rect = canvas_rects[1]
                click_point = (current_rect['left'] + math.floor(current_rect['width']) / 2 + target_x * click_scale, current_rect['top'] + math.floor(current_rect['height']) / 2 - target_y * click_scale)
                drag_mouse(click_point, click_point)
                if evaluate("document.getElementById('trail-square').value") != str(square_count - 1):
                    raise CDPError("clicking a square did not select its center trail")
                evaluate(f"document.getElementById('trail-square').value='all'; document.getElementById('trail-square').dispatchEvent(new Event('change')); document.getElementById('frame-slider').value='{selected_frame}'; document.getElementById('frame-slider').dispatchEvent(new Event('input'))")

                if frame_count >= 3:
                    evaluate("document.getElementById('range-start').value='1'; document.getElementById('range-start').dispatchEvent(new Event('change'))")
                    end_index = min(3, frame_count - 1)
                    evaluate(f"document.getElementById('range-end').value='{end_index}'; document.getElementById('range-end').dispatchEvent(new Event('change')); document.getElementById('frame-slider').value='1'; document.getElementById('frame-slider').dispatchEvent(new Event('input')); document.getElementById('play-pause').click()")
                    range_samples = evaluate("new Promise(resolve=>{const samples=[];const timer=setInterval(()=>samples.push(Number(document.getElementById('frame-slider').value)),20);setTimeout(()=>{clearInterval(timer);resolve(samples)},600)})", await_promise=True)
                    if not all(1 <= index <= end_index for index in range_samples) or evaluate("document.getElementById('play-pause').textContent") != 'Play' or evaluate("document.getElementById('frame-slider').value") != str(end_index):
                        raise CDPError("one-shot playback escaped the A/B range or did not stop on B")
                    evaluate("document.getElementById('playback-mode').value='loop'; document.getElementById('playback-mode').dispatchEvent(new Event('change')); document.getElementById('play-pause').click()")
                    loop_samples = evaluate("new Promise(resolve=>{const samples=[];const timer=setInterval(()=>samples.push(Number(document.getElementById('frame-slider').value)),20);setTimeout(()=>{clearInterval(timer);resolve(samples)},600)})", await_promise=True)
                    if not all(1 <= index <= end_index for index in loop_samples) or not any(before > after for before, after in zip(loop_samples, loop_samples[1:])):
                        raise CDPError("loop playback did not wrap from B to A")
                    evaluate("document.getElementById('frame-slider').value='0'; document.getElementById('frame-slider').dispatchEvent(new Event('input'))")
                    time.sleep(0.15)
                    if evaluate("document.getElementById('play-pause').textContent") != 'Play' or evaluate("document.getElementById('frame-slider').value") != '0':
                        raise CDPError("manual navigation did not pause playback outside the A/B range")
                    evaluate("document.getElementById('reset-range').click(); document.getElementById('start-marker').scrollIntoView({block:'center'})")
                    marker_rect = evaluate("(()=>{const r=document.getElementById('marker-track').getBoundingClientRect();const a=document.getElementById('start-marker').getBoundingClientRect();return {left:r.left,width:r.width,x:a.left+a.width/2,y:a.top+a.height/2}})()")
                    drag_mouse((marker_rect['x'], marker_rect['y']), (marker_rect['left'] + 0.35 * marker_rect['width'], marker_rect['y']))
                    if int(evaluate("document.getElementById('range-start').value")) != math.floor(0.35 * (frame_count - 1) + 0.5):
                        raise CDPError("dragging marker A did not update its frame index")
                    end_marker = evaluate("(()=>{const r=document.getElementById('end-marker').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()")
                    drag_mouse((end_marker['x'], end_marker['y']), (marker_rect['left'] + 0.85 * marker_rect['width'], end_marker['y']))
                    if int(evaluate("document.getElementById('range-end').value")) != math.floor(0.85 * (frame_count - 1) + 0.5):
                        raise CDPError("dragging marker B did not update its frame index")
                    evaluate("document.getElementById('playback-mode').value='once'; document.getElementById('playback-mode').dispatchEvent(new Event('change')); document.getElementById('reset-range').click()")
                evaluate(f"document.getElementById('frame-slider').value='{selected_frame}'; document.getElementById('frame-slider').dispatchEvent(new Event('input')); window.scrollTo(0,0)")
                final_svg = capture_svg()
                if final_svg != exported_svg:
                    raise CDPError("restoring viewer controls changed the exported numeric geometry")
                report["center_trails"] = {
                    "all_and_selected_square_coordinates_match": True,
                    "no_future_frames": True,
                    "visibility_and_selection_work": True,
                    "canvas_toggle": trails_hidden,
                    "orientation_labels_do_not_intersect": True,
                    "svg_respects_id_and_orientation_toggles": True,
                    "square_visibility_preserves_trails": True,
                    "legend_unique_colors_match_ids_and_polygons": True,
                    "legend_click_selects_trail": True,
                    "side_caption_outside_canvas": True,
                    "readable_validation_without_raw_json": True,
                    "short_history_and_focus_dimming": True,
                    "container_visibility": True,
                    "scene_zoom_pan_and_wheel": True,
                    "micromovement_zoom_4096_and_fixed_camera": True,
                    "maximum_zoom_65536_preserves_geometry": True,
                    "square_click_selects_trail": True,
                    "ab_markers_once_loop_and_drag": frame_count >= 3,
                }
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
