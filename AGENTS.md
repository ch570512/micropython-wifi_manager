# AGENTS.md

## Architecture

- **Library**: `wifi_manager.py` - the actual module
- **Example**: `main.py` - usage demonstration only
- **Portal UI**: `wifi_manager.html` - served by the AP config portal

## Development Environment

This is a **MicroPython library** targeting ESP32:
- Code cannot be executed or tested locally
- Must be deployed to hardware via MicroPico VS Code extension
- No automated tests, linting, or CI exist
- Type checking uses MicroPython stubs from `~/.micropico-stubs/micropython-esp32-stubs==1.28.0.post4`

## Key Constraints

- Hardware-dependent modules: `machine`, `network`, `micropython.const()`
- Memory-constrained environment: use `gc.collect()` after large operations, catch `MemoryError`
- Constants should use `micropython.const()` for compile-time optimization
- Credentials stored in plaintext JSON file (`wifi_config.json`) on device flash
- AP portal uses hardcoded IP `192.168.4.1` and channel 6

## Verification

The only way to verify changes is to:
1. Deploy to device via MicroPico
2. Run `main.py` on the microcontroller
3. Test the WiFi connection flow and AP portal manually
