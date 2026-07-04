import json
import requests
from websocket import create_connection

class HomeAssistantAPI:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def rest_get(self, path: str):
        response = requests.get(f"{self.url}{path}", headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def ws_call(self, msg_type: str, **kwargs):
        ws_url = self.url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
        ws = create_connection(ws_url, timeout=30)
        greeting = json.loads(ws.recv())
        if greeting.get("type") != "auth_required":
            ws.close()
            raise RuntimeError(f"Unexpected websocket greeting: {greeting}")
        ws.send(json.dumps({"type": "auth", "access_token": self.token}))
        auth = json.loads(ws.recv())
        if auth.get("type") != "auth_ok":
            ws.close()
            raise RuntimeError(f"WebSocket auth failed: {auth}")
        msg_id = 1
        ws.send(json.dumps({"id": msg_id, "type": msg_type, **kwargs}))
        while True:
            response = json.loads(ws.recv())
            if response.get("id") == msg_id:
                ws.close()
                if not response.get("success", False):
                    raise RuntimeError(f"WebSocket call failed: {response}")
                return response.get("result")
