# Code created by Siddharth Ahuja: www.github.com/ahujasid © 2025

import re
import bpy
import mathutils
import json
import threading
import socket
import queue
import time
import requests
import tempfile
import traceback
import os
import shutil
import zipfile
from bpy.props import IntProperty, BoolProperty
import io
from datetime import datetime
import hashlib, hmac, base64
import os.path as osp
from collections import deque
from contextlib import contextmanager, redirect_stdout, suppress
from bpy.app.handlers import persistent

bl_info = {
    "name": "Blender MCP",
    "author": "BlenderMCP",
    "version": (1, 5),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to Claude via MCP",
    "category": "Interface",
}

ADDON_PROTOCOL_VERSION = 4
RODIN_FREE_TRIAL_KEY = "vibecoding"

REQ_HEADERS = requests.utils.default_headers()
REQ_HEADERS.update({"User-Agent": "blender-mcp"})

MAX_EDIT_EVENTS = 256

_IGNORED_OPERATORS = frozenset({
    "view3d.rotate",
    "view3d.move",
    "view3d.zoom",
    "view3d.dolly",
    "view3d.view_axis",
    "view3d.view_orbit",
    "view3d.view_pan",
    "view3d.smoothview",
    "view3d.cursor3d",
    "wm.tool_set_by_id",
    "wm.context_set_value",
    "screen.animation_step",
})

_PATH_PROPERTY_NAMES = frozenset({
    "filepath",
    "filename",
    "directory",
    "filepath_raw",
    "relpath",
})
_PATH_PROPERTY_SUBSTRINGS = ("filepath", "filename", "directory", "_dir", "path")
MAX_OPERATOR_PROPERTY_CHARS = 200
EDIT_POLL_MIN_INTERVAL = 0.1


def _is_path_property(identifier):
    lowered = identifier.lower()
    if lowered in _PATH_PROPERTY_NAMES:
        return True
    return any(token in lowered for token in _PATH_PROPERTY_SUBSTRINGS)


class UserEditRecorder:
    def __init__(self):
        self._events = deque(maxlen=MAX_EDIT_EVENTS)
        self._agent_depth = 0
        self._last_operator_count = 0
        self._seen_baseline = False
        self._last_poll_time = 0.0

    @contextmanager
    def agent_command(self):
        self._agent_depth += 1
        try:
            yield
        finally:
            self._agent_depth = max(0, self._agent_depth - 1)
            self._resync_operator_baseline()

    @property
    def _suppressed(self):
        return self._agent_depth > 0

    def _operator_stack(self):
        try:
            return list(bpy.context.window_manager.operators)
        except Exception:
            return []

    def _resync_operator_baseline(self):
        self._last_operator_count = len(self._operator_stack())
        self._seen_baseline = True

    def poll_operators(self, now=None):
        if self._suppressed:
            return
        now = time.time() if now is None else now
        if (now - self._last_poll_time) < EDIT_POLL_MIN_INTERVAL:
            return
        self._last_poll_time = now
        stack = self._operator_stack()
        count = len(stack)

        if not self._seen_baseline:
            self._last_operator_count = count
            self._seen_baseline = True
            return

        if count <= self._last_operator_count:
            return

        for op in stack[self._last_operator_count:count]:
            self._record_operator(op)
        self._last_operator_count = count

    def _record_operator(self, op):
        try:
            bl_idname = getattr(op, "bl_idname", None)
            if not bl_idname:
                return
            normalized = bl_idname.lower().replace("_ot_", ".", 1)
            if normalized in _IGNORED_OPERATORS:
                return
            self._events.append({
                "kind": "operator",
                "bl_idname": normalized,
                "name": getattr(op, "name", None),
                "properties": self._operator_properties(op),
                "timestamp": time.time(),
            })
        except Exception as e:
            print(f"Manual edit capture: failed to record operator: {e}")

    @staticmethod
    def _operator_properties(op):
        props = {}
        try:
            rna_props = op.properties.bl_rna.properties
        except Exception:
            return props
        for prop in rna_props:
            if prop.identifier == "rna_type":
                continue
            if _is_path_property(prop.identifier):
                continue
            try:
                value = getattr(op.properties, prop.identifier)
            except Exception:
                continue
            if isinstance(value, str):
                props[prop.identifier] = value[:MAX_OPERATOR_PROPERTY_CHARS]
            elif isinstance(value, (bool, int, float)):
                props[prop.identifier] = value
            elif hasattr(value, "__len__") and not isinstance(value, (dict, bytes)):
                try:
                    items = [
                        v[:MAX_OPERATOR_PROPERTY_CHARS] if isinstance(v, str) else v
                        for v in value
                        if isinstance(v, (bool, int, float, str))
                    ]
                    if items and len(items) <= 16:
                        props[prop.identifier] = items
                except Exception:
                    continue
        return props

    def record_undo(self, kind):
        if self._suppressed:
            return
        self._events.append({
            "kind": kind,
            "timestamp": time.time(),
        })
        self._last_operator_count = max(
            self._last_operator_count, len(self._operator_stack())
        )
        self._seen_baseline = True

    def drain(self):
        events = list(self._events)
        self._events.clear()
        return events


_edit_recorder = UserEditRecorder()


def get_edit_recorder():
    return _edit_recorder


@persistent
def _blendermcp_undo_post(scene, depsgraph=None):
    _edit_recorder.record_undo("undo")


@persistent
def _blendermcp_redo_post(scene, depsgraph=None):
    _edit_recorder.record_undo("redo")


@persistent
def _blendermcp_depsgraph_post(scene, depsgraph=None):
    _edit_recorder.poll_operators()


def _telemetry_consent_enabled():
    try:
        addon_prefs = bpy.context.preferences.addons.get(__name__)
        if not addon_prefs:
            return False
        return bool(addon_prefs.preferences.telemetry_consent)
    except Exception:
        return False


def _register_edit_capture_handlers():
    if not _telemetry_consent_enabled():
        _unregister_edit_capture_handlers()
        return False

    handlers = [
        (bpy.app.handlers.undo_post, _blendermcp_undo_post),
        (bpy.app.handlers.redo_post, _blendermcp_redo_post),
        (bpy.app.handlers.depsgraph_update_post, _blendermcp_depsgraph_post),
    ]
    for handler_list, fn in handlers:
        if fn not in handler_list:
            handler_list.append(fn)
    return True


def sync_edit_capture_handlers():
    try:
        server_running = bool(
            getattr(bpy.types, "blendermcp_server", None)
            and bpy.types.blendermcp_server.running
        )
    except Exception:
        server_running = False

    if not server_running:
        _unregister_edit_capture_handlers()
        return False
    return _register_edit_capture_handlers()


def _unregister_edit_capture_handlers():
    handlers = [
        (bpy.app.handlers.undo_post, _blendermcp_undo_post),
        (bpy.app.handlers.redo_post, _blendermcp_redo_post),
        (bpy.app.handlers.depsgraph_update_post, _blendermcp_depsgraph_post),
    ]
    for handler_list, fn in handlers:
        with suppress(ValueError):
            handler_list.remove(fn)


def get_blendermcp_addon_preferences(context=None):
    if context is None:
        context = bpy.context
    addon = context.preferences.addons.get(__name__)
    return addon.preferences if addon else None


class BlenderMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
        self.command_queue = queue.Queue()
        self._clients = set()
        self._clients_lock = threading.Lock()

    def _get_config_value(self, scene_attr, pref_attr=None, env_var=None):
        prefs = get_blendermcp_addon_preferences()
        if prefs and pref_attr:
            pref_value = getattr(prefs, pref_attr, "")
            if pref_value:
                return pref_value

        scene_value = getattr(bpy.context.scene, scene_attr, "")
        if scene_value:
            return scene_value

        if env_var:
            env_value = os.getenv(env_var, "")
            if env_value:
                return env_value
        return ""

    def start(self):
        if bpy.app.background:
            print("BlenderMCP: cannot start server in background mode")
            return

        if self.running:
            print("Server is already running")
            return

        self.running = True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)

            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()

            _register_edit_capture_handlers()

            if not bpy.app.timers.is_registered(self._drain_command_queue):
                bpy.app.timers.register(self._drain_command_queue, persistent=True)

            print(f"BlenderMCP server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False
        _unregister_edit_capture_handlers()
        get_edit_recorder().drain()

        try:
            if bpy.app.timers.is_registered(self._drain_command_queue):
                bpy.app.timers.unregister(self._drain_command_queue)
        except Exception:
            pass

        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        with self._clients_lock:
            clients = list(self._clients)
            self._clients.clear()
        for client in clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                client.close()
            except Exception:
                pass

        while True:
            try:
                self.command_queue.get_nowait()
            except queue.Empty:
                break

        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
            self.server_thread = None

        print("BlenderMCP server stopped")

    def _server_loop(self):
        self.socket.settimeout(1.0)
        while self.running:
            try:
                try:
                    client, address = self.socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    time.sleep(0.5)
            except Exception as e:
                if not self.running:
                    break
                time.sleep(0.5)

    def _drain_command_queue(self):
        if not self.running:
            return None

        while True:
            try:
                command, client = self.command_queue.get_nowait()
            except queue.Empty:
                break

            try:
                response = self.execute_command(command)
                response_json = json.dumps(response)
            except Exception as e:
                response_json = json.dumps({"status": "error", "message": str(e)})

            try:
                client.sendall(response_json.encode('utf-8'))
            except Exception:
                pass

        return 0.05

    def _handle_client(self, client):
        client.settimeout(1.0)
        with self._clients_lock:
            self._clients.add(client)
        buffer = b''

        try:
            while self.running:
                try:
                    data = client.recv(8192)
                    if not data:
                        break
                    buffer += data
                    try:
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''
                        self.command_queue.put((command, client))
                    except json.JSONDecodeError:
                        pass
                except socket.timeout:
                    continue
                except Exception:
                    break
        finally:
            with self._clients_lock:
                self._clients.discard(client)
            try:
                client.close()
            except:
                pass

    def execute_command(self, command):
        try:
            with get_edit_recorder().agent_command():
                return self._execute_command_internal(command)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        cmd_type = command.get("type")
        params = command.get("params", {})

        if cmd_type == "ping":
            return {"status": "success", "result": {"pong": True}}

        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "get_viewport_screenshot": self.get_viewport_screenshot,
            "execute_code": self.execute_code,
            "drain_human_activity": self.drain_human_activity,
            "get_telemetry_consent": self.get_telemetry_consent,
            "set_telemetry_consent": self.set_telemetry_consent,
        }

        handler = handlers.get(cmd_type)
        if handler:
            try:
                result = handler(**params)
                return {"status": "success", "result": result}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    def execute_code(self, code):
        """Execute arbitrary Python code in Blender."""
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        exec_globals = {
            "bpy": bpy,
            "mathutils": mathutils,
            "context": bpy.context,
        }
        
        try:
            with redirect_stdout(stdout_capture):
                exec(code, exec_globals)
            return {
                "status": "success",
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc(),
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue()
            }

    def get_scene_info(self):
        scene_info = {
            "name": bpy.context.scene.name,
            "object_count": len(bpy.context.scene.objects),
            "objects": [],
            "materials_count": len(bpy.data.materials),
        }
        for i, obj in enumerate(bpy.context.scene.objects):
            if i >= 30:
                break
            scene_info["objects"].append({
                "name": obj.name,
                "type": obj.type,
                "location": [round(float(obj.location.x), 2), round(float(obj.location.y), 2), round(float(obj.location.z), 2)]
            })
        return scene_info

    def get_object_info(self, name):
        obj = bpy.data.objects.get(name)
        if not obj:
            return {"error": f"Object '{name}' not found"}
        return {
            "name": obj.name,
            "type": obj.type,
            "location": [float(obj.location.x), float(obj.location.y), float(obj.location.z)],
            "rotation": [float(obj.rotation_euler.x), float(obj.rotation_euler.y), float(obj.rotation_euler.z)],
            "scale": [float(obj.scale.x), float(obj.scale.y), float(obj.scale.z)]
        }

    def get_viewport_screenshot(self, filepath=None):
        if not filepath:
            filepath = os.path.join(tempfile.gettempdir(), "blender_viewport.png")
        bpy.ops.render.opengl(write_still=True)
        bpy.data.images['Render Result'].save_render(filepath)
        return {"filepath": filepath}

    def drain_human_activity(self):
        return {"events": get_edit_recorder().drain()}

    def get_telemetry_consent(self):
        return {"consent": _telemetry_consent_enabled()}

    def set_telemetry_consent(self, consent):
        prefs = get_blendermcp_addon_preferences()
        if prefs:
            prefs.telemetry_consent = bool(consent)
            sync_edit_capture_handlers()
            return {"consent": bool(consent)}
        return {"error": "Preferences not available"}


class BLENDERMCP_PT_panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BlenderMCP'

    def draw(self, context):
        layout = self.layout
        server = getattr(bpy.types, "blendermcp_server", None)
        running = server and server.running

        box = layout.box()
        col = box.column(align=True)
        if running:
            col.label(text=f"Status: Running (Port {server.port})", icon='CHECKMARK')
            col.operator("blendermcp.stop_server", text="Stop Server", icon='PAUSE')
        else:
            col.label(text="Status: Stopped", icon='X')
            col.operator("blendermcp.start_server", text="Start Server", icon='PLAY')


class BLENDERMCP_OT_start_server(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Start BlenderMCP Server"

    def execute(self, context):
        if not hasattr(bpy.types, "blendermcp_server") or bpy.types.blendermcp_server is None:
            bpy.types.blendermcp_server = BlenderMCPServer()
        bpy.types.blendermcp_server.start()
        return {'FINISHED'}


class BLENDERMCP_OT_stop_server(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop BlenderMCP Server"

    def execute(self, context):
        if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
            bpy.types.blendermcp_server.stop()
        return {'FINISHED'}


classes = (
    BLENDERMCP_PT_panel,
    BLENDERMCP_OT_start_server,
    BLENDERMCP_OT_stop_server,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.blendermcp_server = BlenderMCPServer()


def unregister():
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        bpy.types.blendermcp_server.stop()
        del bpy.types.blendermcp_server

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
