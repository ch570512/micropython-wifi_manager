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

import wifi_manager


def main():
    wifi = wifi_manager.connect("Wifi-AP")
    print(wifi.status)


if __name__ == "__main__":
    main()
