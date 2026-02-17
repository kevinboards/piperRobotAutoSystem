"""
Piper Automation System - Unified Web Server
Single entry point: CAN bus activation, Piper SDK init, HTTP + WebSocket server.
"""

import asyncio
import json
import sys
import os
import subprocess
import time
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from aiohttp import web
import websockets

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "piper_sdk"))

# Import Piper SDK
try:
    from piper_sdk import C_PiperInterface_V2
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

# Import project modules
from recorder import PiperRecorder
from player import PiperPlayer
from ppr_file_handler import list_recordings, get_recording_info, read_ppr_file
from timeline import Timeline, TimelineClip, TimelineManager
from timeline_player import TimelinePlayer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("server")

HOST = "0.0.0.0"
HTTP_PORT = 8000
WS_PORT = 8080
WEB_DIR = Path(__file__).parent / "web"
CAN_ACTIVATE_SCRIPT = Path(__file__).parent / "piper_sdk" / "piper_sdk" / "can_activate.sh"
STATUS_UPDATE_HZ = 5


# ---------------------------------------------------------------------------
# CAN Bus Activation
# ---------------------------------------------------------------------------

def activate_can_bus(can_name: str = "can0", bitrate: int = 1000000) -> bool:
    """Activate CAN bus interface. Returns True on success."""
    if sys.platform == "win32":
        logger.warning("CAN bus activation skipped on Windows (demo mode)")
        return False

    # Try the SDK's can_activate.sh first
    if CAN_ACTIVATE_SCRIPT.exists():
        logger.info(f"Running CAN activation script: {CAN_ACTIVATE_SCRIPT}")
        try:
            result = subprocess.run(
                ["sudo", "bash", str(CAN_ACTIVATE_SCRIPT), can_name, str(bitrate)],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                logger.info("CAN bus activated via script")
                return True
            else:
                logger.warning(f"CAN script failed: {result.stderr.strip()}")
        except Exception as e:
            logger.warning(f"CAN script error: {e}")

    # Fallback: direct ip link commands
    logger.info("Attempting direct CAN bus activation via ip link")
    try:
        subprocess.run(["sudo", "ip", "link", "set", can_name, "down"],
                       capture_output=True, timeout=5)
        subprocess.run(["sudo", "ip", "link", "set", can_name, "type", "can",
                         "bitrate", str(bitrate)],
                       capture_output=True, timeout=5)
        result = subprocess.run(["sudo", "ip", "link", "set", can_name, "up"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info(f"CAN bus {can_name} activated at {bitrate} bps")
            return True
        else:
            logger.warning(f"ip link failed: {result.stderr.strip()}")
    except Exception as e:
        logger.warning(f"Direct CAN activation failed: {e}")

    return False


# ---------------------------------------------------------------------------
# Piper Robot Connection
# ---------------------------------------------------------------------------

def connect_robot() -> Optional['C_PiperInterface_V2']:
    """Connect to Piper robot. Returns interface or None."""
    if not SDK_AVAILABLE:
        logger.warning("Piper SDK not available - running in demo mode")
        return None
    try:
        piper = C_PiperInterface_V2()
        piper.ConnectPort()
        logger.info("Connected to Piper robot")
        return piper
    except Exception as e:
        logger.error(f"Robot connection failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Main Server
# ---------------------------------------------------------------------------

class PiperServer:
    def __init__(self, piper: Optional['C_PiperInterface_V2'] = None):
        self.piper = piper
        self.ws_clients: set = set()

        # State
        self.recorder: Optional[PiperRecorder] = None
        self.player: Optional[PiperPlayer] = None
        self.timeline_player: Optional[TimelinePlayer] = None
        self.timeline_manager = TimelineManager()

        self.is_recording = False
        self.is_playing = False
        self._status_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # -- WebSocket broadcast ------------------------------------------------

    async def broadcast(self, data: dict):
        """Send JSON message to all connected web clients."""
        if not self.ws_clients:
            return
        msg = json.dumps(data)
        stale = set()
        for ws in self.ws_clients:
            try:
                await ws.send(msg)
            except Exception:
                stale.add(ws)
        self.ws_clients -= stale

    async def send(self, ws, data: dict):
        """Send JSON message to a single client."""
        try:
            await ws.send(json.dumps(data))
        except Exception:
            pass

    # -- Status helpers -----------------------------------------------------

    def _get_joint_positions(self) -> list:
        """Read current joint positions from robot."""
        if not self.piper:
            return [0.0] * 6
        try:
            jd = self.piper.GetArmJointMsgs()
            return [
                jd.joint_state.joint_1 * 0.001,
                jd.joint_state.joint_2 * 0.001,
                jd.joint_state.joint_3 * 0.001,
                jd.joint_state.joint_4 * 0.001,
                jd.joint_state.joint_5 * 0.001,
                jd.joint_state.joint_6 * 0.001,
            ]
        except Exception:
            return [0.0] * 6

    def _build_status(self) -> dict:
        return {
            "type": "status",
            "connected": self.piper is not None,
            "sdk_available": SDK_AVAILABLE,
            "recording": self.is_recording,
            "playing": self.is_playing,
            "joints": self._get_joint_positions(),
        }

    # -- Periodic status broadcast ------------------------------------------

    async def _status_loop(self):
        """Broadcast status at STATUS_UPDATE_HZ while recording or playing."""
        while True:
            try:
                if self.is_recording and self.recorder:
                    stats = self.recorder.get_recording_stats()
                    await self.broadcast({
                        "type": "recording_progress",
                        "samples": stats.get("sample_count", 0),
                        "duration": round(stats.get("duration_sec", 0), 2),
                        "rate": round(stats.get("current_rate", 0), 1),
                    })
                elif self.is_playing:
                    if self.player and self.player.is_playing():
                        info = self.player.get_playback_info()
                        await self.broadcast({
                            "type": "playback_progress",
                            "progress": round(info.get("progress_percent", 0), 1),
                            "current_sample": info.get("current_sample", 0),
                            "total_samples": info.get("total_samples", 0),
                            "status": "playing",
                        })
                    elif self.timeline_player and self.timeline_player.is_playing:
                        tp = self.timeline_player.get_progress()
                        await self.broadcast({
                            "type": "playback_progress",
                            "progress": round(tp.get("progress_percent", 0), 1),
                            "current_position": round(tp.get("current_position", 0), 2),
                            "total_duration": round(tp.get("total_duration", 0), 2),
                            "status": "playing",
                        })
                    else:
                        # Playback finished
                        self.is_playing = False
                        await self.broadcast({"type": "timeline_complete"})
            except Exception as e:
                logger.debug(f"Status loop error: {e}")
            await asyncio.sleep(1.0 / STATUS_UPDATE_HZ)

    # -- Command handlers ---------------------------------------------------

    async def handle_message(self, ws, msg: dict):
        """Route incoming WebSocket message to handler."""
        msg_type = msg.get("type", "")
        handler = {
            "get_status": self._handle_get_status,
            "get_recordings": self._handle_get_recordings,
            "start_recording": self._handle_start_recording,
            "stop_recording": self._handle_stop_recording,
            "load_recording": self._handle_load_recording,
            "start_playback": self._handle_start_playback,
            "stop_playback": self._handle_stop_playback,
            "pause_playback": self._handle_pause_playback,
            "resume_playback": self._handle_resume_playback,
            "play_timeline": self._handle_play_timeline,
            "save_timeline": self._handle_save_timeline,
            "load_timeline": self._handle_load_timeline,
            "list_timelines": self._handle_list_timelines,
            "delete_recording": self._handle_delete_recording,
        }.get(msg_type)

        if handler:
            try:
                await handler(ws, msg)
            except Exception as e:
                logger.error(f"Handler error [{msg_type}]: {e}")
                await self.send(ws, {"type": "error", "message": str(e)})
        else:
            await self.send(ws, {"type": "error", "message": f"Unknown message type: {msg_type}"})

    async def _handle_get_status(self, ws, msg):
        await self.send(ws, self._build_status())

    async def _handle_get_recordings(self, ws, msg):
        recordings = []
        for name in list_recordings():
            info = get_recording_info(str(Path("recordings") / name))
            recordings.append({
                "name": name,
                "duration": round(info.get("duration_sec", 0), 2),
                "samples": info.get("sample_count", 0),
                "created": info.get("created", ""),
            })
        await self.send(ws, {"type": "recordings_list", "recordings": recordings})

    async def _handle_start_recording(self, ws, msg):
        if not self.piper:
            await self.send(ws, {"type": "error", "message": "Robot not connected"})
            return
        if self.is_recording:
            await self.send(ws, {"type": "error", "message": "Already recording"})
            return

        name = msg.get("name")
        self.recorder = PiperRecorder(self.piper, sample_rate=200)
        filepath = self.recorder.start_recording(filename=name, description="Web recording")
        self.is_recording = True
        await self.broadcast({"type": "log", "level": "info", "message": f"Recording started: {Path(filepath).name}"})
        await self.broadcast(self._build_status())

    async def _handle_stop_recording(self, ws, msg):
        if not self.is_recording or not self.recorder:
            await self.send(ws, {"type": "error", "message": "Not recording"})
            return

        stats = self.recorder.stop_recording()
        self.is_recording = False
        self.recorder = None
        await self.broadcast({
            "type": "log", "level": "info",
            "message": f"Recording saved: {stats.get('filename', '?')} ({stats.get('sample_count', 0)} samples, {stats.get('duration_sec', 0):.1f}s)"
        })
        await self.broadcast(self._build_status())

    async def _handle_load_recording(self, ws, msg):
        """Load a recording and prepare for single-file playback."""
        name = msg.get("name", "")
        filepath = Path("recordings") / name
        if not filepath.exists():
            await self.send(ws, {"type": "error", "message": f"Recording not found: {name}"})
            return
        if not self.piper:
            await self.send(ws, {"type": "error", "message": "Robot not connected"})
            return

        self.player = PiperPlayer(self.piper)
        info = self.player.load_recording(str(filepath))
        await self.send(ws, {
            "type": "recording_loaded",
            "name": name,
            "duration": round(info.get("duration_sec", 0), 2),
            "samples": info.get("sample_count", 0),
        })

    async def _handle_start_playback(self, ws, msg):
        """Start playback of previously loaded recording."""
        if not self.piper:
            await self.send(ws, {"type": "error", "message": "Robot not connected"})
            return
        if self.is_playing:
            await self.send(ws, {"type": "error", "message": "Already playing"})
            return

        speed = float(msg.get("speed", 1.0))

        # If a recording name is provided, load it first
        name = msg.get("name")
        if name:
            filepath = Path("recordings") / name
            if not filepath.exists():
                await self.send(ws, {"type": "error", "message": f"Recording not found: {name}"})
                return
            self.player = PiperPlayer(self.piper)
            self.player.load_recording(str(filepath))

        if not self.player or not self.player.is_loaded():
            await self.send(ws, {"type": "error", "message": "No recording loaded"})
            return

        self.player.start_playback(speed_multiplier=speed)
        self.is_playing = True
        await self.broadcast({"type": "log", "level": "info", "message": f"Playback started at {speed}x"})
        await self.broadcast(self._build_status())

    async def _handle_stop_playback(self, ws, msg):
        if self.player and self.player.is_playing():
            self.player.stop_playback()
        if self.timeline_player and self.timeline_player.is_playing:
            self.timeline_player.stop()
        self.is_playing = False
        await self.broadcast({"type": "log", "level": "info", "message": "Playback stopped"})
        await self.broadcast(self._build_status())

    async def _handle_pause_playback(self, ws, msg):
        if self.player and self.player.is_playing():
            self.player.pause_playback()
            await self.broadcast({"type": "log", "level": "info", "message": "Playback paused"})

    async def _handle_resume_playback(self, ws, msg):
        if self.player and self.player.is_paused():
            self.player.resume_playback()
            await self.broadcast({"type": "log", "level": "info", "message": "Playback resumed"})

    async def _handle_play_timeline(self, ws, msg):
        """Play a timeline (list of clips with timing)."""
        if not self.piper:
            await self.send(ws, {"type": "error", "message": "Robot not connected"})
            return
        if self.is_playing:
            await self.send(ws, {"type": "error", "message": "Already playing"})
            return

        timeline_data = msg.get("timeline")
        speed = float(msg.get("speed", 1.0))

        if not timeline_data:
            await self.send(ws, {"type": "error", "message": "No timeline data provided"})
            return

        # Build Timeline from JSON
        timeline = Timeline.from_dict(timeline_data)
        if not timeline.enabled_clips:
            await self.send(ws, {"type": "error", "message": "Timeline has no enabled clips"})
            return

        loop = asyncio.get_event_loop()

        def on_complete():
            asyncio.run_coroutine_threadsafe(
                self.broadcast({"type": "timeline_complete"}), loop
            )
            self.is_playing = False

        self.timeline_player = TimelinePlayer(
            self.piper, timeline, global_speed=speed,
            on_complete=on_complete,
        )
        self.is_playing = True

        # Run in background thread (TimelinePlayer.play_sync is blocking)
        thread = threading.Thread(target=self.timeline_player.play_sync, daemon=True)
        thread.start()

        await self.broadcast({"type": "log", "level": "info", "message": f"Timeline playback started at {speed}x"})
        await self.broadcast(self._build_status())

    async def _handle_save_timeline(self, ws, msg):
        name = msg.get("name", "")
        data = msg.get("data")
        if not name or not data:
            await self.send(ws, {"type": "error", "message": "Name and data required"})
            return

        tl_path = self.timeline_manager.get_timeline_path(name)
        tl_path.parent.mkdir(exist_ok=True)
        with open(tl_path, "w") as f:
            json.dump(data, f, indent=2)
        await self.send(ws, {"type": "log", "level": "info", "message": f"Timeline saved: {name}"})

    async def _handle_load_timeline(self, ws, msg):
        name = msg.get("name", "")
        tl_path = self.timeline_manager.get_timeline_path(name)
        if not tl_path.exists():
            await self.send(ws, {"type": "error", "message": f"Timeline not found: {name}"})
            return
        with open(tl_path, "r") as f:
            data = json.load(f)
        await self.send(ws, {"type": "timeline_loaded", "name": name, "data": data})

    async def _handle_list_timelines(self, ws, msg):
        names = self.timeline_manager.list_timelines()
        await self.send(ws, {"type": "timelines_list", "timelines": names})

    async def _handle_delete_recording(self, ws, msg):
        name = msg.get("name", "")
        filepath = Path("recordings") / name
        if not filepath.exists():
            await self.send(ws, {"type": "error", "message": f"Recording not found: {name}"})
            return
        filepath.unlink()
        await self.broadcast({"type": "log", "level": "info", "message": f"Deleted recording: {name}"})

    # -- WebSocket handler --------------------------------------------------

    async def ws_handler(self, ws, path=None):
        """Handle a WebSocket client connection."""
        logger.info("WebSocket client connected")
        self.ws_clients.add(ws)
        try:
            # Send initial status
            await self.send(ws, self._build_status())

            async for raw in ws:
                try:
                    msg = json.loads(raw)
                    await self.handle_message(ws, msg)
                except json.JSONDecodeError:
                    await self.send(ws, {"type": "error", "message": "Invalid JSON"})
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.ws_clients.discard(ws)
            logger.info("WebSocket client disconnected")

    # -- HTTP static file server --------------------------------------------

    async def start_http_server(self):
        """Serve static files from web/ directory."""
        app = web.Application()

        if WEB_DIR.exists():
            app.router.add_get("/", self._serve_index)
            app.router.add_static("/", WEB_DIR, show_index=False)
            logger.info(f"Serving static files from {WEB_DIR}")
        else:
            app.router.add_get("/", self._serve_placeholder)
            logger.warning(f"Web directory not found: {WEB_DIR}")

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, HOST, HTTP_PORT)
        await site.start()
        logger.info(f"HTTP server listening on http://{HOST}:{HTTP_PORT}")

    async def _serve_index(self, request):
        index = WEB_DIR / "index.html"
        if index.exists():
            return web.FileResponse(index)
        return web.Response(text="Piper Automation System - web/index.html not found", status=404)

    async def _serve_placeholder(self, request):
        return web.Response(
            text="<h1>Piper Automation System</h1><p>Web UI not yet deployed. Place files in web/ directory.</p>",
            content_type="text/html"
        )

    # -- Start everything ---------------------------------------------------

    async def start_ws_server(self):
        """Start WebSocket server."""
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        async with websockets.serve(self.ws_handler, HOST, WS_PORT):
            logger.info(f"WebSocket server listening on ws://{HOST}:{WS_PORT}")
            await asyncio.Future()  # run forever

    async def run(self):
        """Start HTTP server, WebSocket server, and status loop."""
        self._loop = asyncio.get_event_loop()
        self._status_task = asyncio.create_task(self._status_loop())
        await asyncio.gather(
            self.start_http_server(),
            self.start_ws_server(),
        )


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Piper Automation System - Web Server")
    print("=" * 60)

    # Step 1: CAN bus activation
    print("\n[1/3] Activating CAN bus...")
    can_ok = activate_can_bus()
    if can_ok:
        print("  CAN bus: OK")
    else:
        print("  CAN bus: SKIPPED (demo mode)")

    # Step 2: Connect to robot
    print("\n[2/3] Connecting to Piper robot...")
    piper = connect_robot()
    if piper:
        print("  Robot: CONNECTED")
    else:
        print("  Robot: NOT CONNECTED (demo mode)")

    # Step 3: Start servers
    print(f"\n[3/3] Starting servers...")
    print(f"  HTTP:      http://{HOST}:{HTTP_PORT}")
    print(f"  WebSocket: ws://{HOST}:{WS_PORT}")
    print("=" * 60)

    server = PiperServer(piper)

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\nServer stopped by user")


if __name__ == "__main__":
    main()
