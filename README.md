# WiFi Manager for MicroPython
<a href="https://www.buymeacoffee.com/ch570512" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 150px !important;"></a>

Flow on boot:
1. Try to connect using saved (not encrypted) credentials from _CONFIG_FILE
2. If connected → return WLAN interface to caller
3. If no saved credentials or connection fails:
   - Start an Access Point _AP_SSID
   - Serve a web portal at _AP_IP where user enters SSID + password
   - Save credentials to "wifi_config.json"
   - Reboot the microcontroller

<img src="images/wifi_manager.jpg" width="320
" alt="Wifi-Manager">

Copyright © 2026 [ch570512](https://github.com/ch570512) - Licensed under [GPLv3+](https://www.gnu.org/licenses/gpl-3.0.html) or later.
