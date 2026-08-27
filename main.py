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

import wifi_manager


def _callback_onApActivated(ssid: str, ip: str) -> None:
    """WiFi manager callback: The configuration AP portal is active."""
    print(f"📡 AP active: '{ssid}' → http://{ip}/")


def main():
    """Call WiFi manager"""
    wifi = wifi_manager.connect("WiFi-AP", on_ap=_callback_onApActivated)
    print(wifi.status)


if __name__ == "__main__":
    main()
