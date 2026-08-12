# WiFi Manager for MicroPython
# Copyright (C) 2026 by ch570512
# @created 22.07.2026
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Flow on boot:
# 1. Try to connect using saved (not encrypted) credentials from _CONFIG_FILE
# 2. If connected → return WLAN interface to caller
# 3. If no saved credentials or connection fails:
#    - Start an Access Point _AP_SSID
#    - Serve a web portal at _AP_IP where user enters SSID + password
#    - Save credentials to "wifi_config.json"
#    - Reboot the microcontroller

from micropython import const
import gc
import json
import machine
import network
import socket
import time

_CONFIG_FILE = const("wifi_config.json")
_AP_SSID = const("MicroPython-Wifi")
_AP_IP = const("192.168.4.1")

_HTTP_OK = const(b"HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n")
_PORTAL_FILE = const("wifi_manager.html")

_portal_html_cache = None


def _load_portal_html() -> str:
    """Load the AP portal HTML template from flash. Cached after first read."""
    global _portal_html_cache
    if _portal_html_cache is None:
        with open(_PORTAL_FILE, "r") as f:
            _portal_html_cache = f.read()
    return _portal_html_cache


def load_credentials() -> dict | None:
    """Load saved WiFi credentials from flash file. Returns dict or None."""
    try:
        with open(_CONFIG_FILE, "r") as f:
            data = json.load(f)
            ssid = data.get("ssid", "").strip()
            if ssid:
                print(f"📂 Loaded credentials for '{ssid}'")
                return {"ssid": ssid, "password": data.get("password", "")}
    except (OSError, ValueError):
        pass
    return None


def save_credentials(ssid: str, password: str) -> None:
    """Persist WiFi credentials to flash file."""
    try:
        with open(_CONFIG_FILE, "w") as f:
            json.dump({"ssid": ssid, "password": password}, f)
        print(f"💾 Saved credentials for '{ssid}'")
    except OSError as e:
        print(f"❌ Failed to save credentials: {e}")


def _ap_page(networks: list) -> str:
    """HTML page for the WiFi configuration portal. Expects list of (ssid, rssi)."""
    net_rows = ""
    for ssid, rssi in networks:
        escaped: str = (
            ssid.replace("&", "&amp;").replace("<", "&lt;").replace("'", "\\'")
        )
        # Signal-strength bars from RSSI
        if rssi >= -55:
            bars = "▂▄▆█"
        elif rssi >= -67:
            bars = "▂▄▆▁"
        elif rssi >= -75:
            bars = "▂▄▁▁"
        else:
            bars = "▂▁▁▁"
        net_rows += (
            '<div class="net-item" onclick="setSsid(\'%s\')">'
            '\U0001f6dc %s <span style="float:right;color:#888;font-size:.75rem">%s</span>'
            "</div>\n"
        ) % (escaped, escaped, bars)
    if not net_rows:
        net_rows = '<div class="net-item net-none">No networks found</div>\n'
    return _load_portal_html().replace("{{NETWORKS}}", net_rows)


def _url_decode(s: str) -> str:
    """Decode percent-encoded and plus-escaped string."""
    result = []
    i = 0
    while i < len(s):
        if s[i] == "+":
            result.append(" ")
        elif s[i] == "%" and i + 2 < len(s):
            try:
                result.append(chr(int(s[i + 1 : i + 3], 16)))
                i += 2
            except ValueError:
                result.append(s[i])
        else:
            result.append(s[i])
        i += 1
    return "".join(result)


def _parse_post(body: str) -> dict:
    """Parse URL-encoded form body."""
    params: dict = {}
    for pair in body.split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            params[_url_decode(k)] = _url_decode(v)
    return params


def _handle(client, networks: list) -> bool:
    """Handle a single HTTP request.

    Returns True if credentials were saved (caller should reboot).
    """
    try:
        req: str = client.recv(1024).decode()
        if not req:
            return False

        method = req.split(" ", 1)[0]
        path = req.split(" ", 2)[1]

        if method == "GET" and "rescan" in path:
            networks[:] = _scan_networks()
            print(f"🔄 Rescan: {len(networks)} network(s)")

        if method == "POST":
            headers, _, body = req.partition("\r\n\r\n")
            clen: int = 0
            for line in headers.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    clen = int(line.split(":", 1)[1].strip())
            while len(body) < clen:
                body += client.recv(clen - len(body)).decode()

            params: dict = _parse_post(body)
            ssid: str = params.get("ssid", "").strip()
            password: str = params.get("password", "")

            if ssid:
                save_credentials(ssid, password)
                return True  # Signal: reboot needed

        html = _ap_page(networks)
        client.sendall(_HTTP_OK + html.encode())
        return False
    except Exception as e:
        print(f"⚠️ WiFi config server error: {e}")
        return False
    finally:
        client.close()


def _start_ap(ap_ssid: str = _AP_SSID) -> network.WLAN:
    """Start the microcontroller in Access Point mode on channel 6."""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ap_ssid, authmode=network.AUTH_OPEN, channel=6)
    # Give it a moment to become active
    for _ in range(20):
        if ap.active():
            break
        time.sleep(0.25)
    return ap


def _scan_networks() -> list:
    """Scan for available WiFi networks.

    Returns list of ``(ssid, rssi)`` tuples sorted by signal strength
    (strongest / least negative RSSI first).
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(0.5)
    # Deduplicate: keep the strongest RSSI for each SSID
    nets: dict = {}
    try:
        results = wlan.scan()
        for ap in results:
            ssid = ap[0].decode() if isinstance(ap[0], bytes) else ap[0]
            rssi = ap[3]
            if ssid and rssi > nets.get(ssid, -100):
                nets[ssid] = rssi
        del results
        gc.collect()
    except Exception as e:
        print(f"⚠️ Scan failed: {e}")
    return sorted(nets.items(), key=lambda x: x[1], reverse=True)


def _config_portal(networks: list, ap_ssid: str = _AP_SSID) -> None:
    """Run the AP + web portal until the user submits valid credentials."""
    ap = _start_ap(ap_ssid)

    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print(f"🌐 Config portal  →  http://{_AP_IP}/")

    reboot: bool = False
    while not reboot:
        try:
            client, addr = s.accept()
            print(f"   Client connected: {addr}")
            reboot = _handle(client, networks)
        except Exception as e:
            print(f"⚠️ Portal error: {e}")
            time.sleep(1)

    s.close()
    ap.active(False)
    print("🔁 Rebooting…")
    machine.reset()


def connect(ap_ssid: str = _AP_SSID) -> network.WLAN:
    """Main entry point: try saved WiFi, fall back to AP config portal.

    Args:
        ap_ssid: SSID for the configuration AP (default: MicroPython-Wifi).

    Returns a connected ``network.WLAN`` interface (STA_IF).
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=network.WLAN.PM_NONE)

    creds: dict | None = load_credentials()
    if creds:
        wlan.connect(creds["ssid"], creds["password"])
        timeout: int = 15
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if wlan.isconnected():
            print(f"✅ WiFi connected ({wlan.ifconfig()[0]})")
            return wlan

        print(f"❌ Connection to '{creds['ssid']}' failed (status={wlan.status()})")

    # Scan for available networks before deactivating STA
    networks: list = _scan_networks()
    print(f"🛜 Found {len(networks)} network{'s' if len(networks) != 1 else ''}")

    # Clean up STA interface before starting AP to avoid radio conflicts
    wlan.disconnect()
    wlan.active(False)

    print("📡 No (valid) saved network")
    _config_portal(networks, ap_ssid)
    # Never reaches here — machine.reset() is called inside _config_portal
    return wlan
