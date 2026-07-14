#!/usr/bin/env python3
"""Generate ESPHome YAML configs and C++ device table from device JSON files."""
import json
import glob
from pathlib import Path


# ============================================================
# YAML fragment constants
# ============================================================
ESP32_BLOCK = """esp32:
  board: esp32dev
  flash_size: 4MB
  framework:
    type: esp-idf
    sdkconfig_options:
      CONFIG_FREERTOS_UNICORE: y
      CONFIG_BT_ENABLED: y
      CONFIG_BT_BLE_ENABLED: y
logger:
  baud_rate: 0"""

WIFI_BLOCK = """wifi:
  ssid: "CC"
  password: "chen1122"
  fast_connect: true
  power_save_mode: none
  ap:
    ssid: "CT1 Fallback"
    password: "12345678"
captive_portal:
web_server:"""

COMMON_TAIL = """ota:
  - platform: esphome
external_components:
  - source:
      type: local
      path: components
ble_gateway:
  id: ct1_ble
"""

BASE_TEMPLATE = f"""esphome:
  name: {{name}}
  friendly_name: {{fn}}
{ESP32_BLOCK}
{WIFI_BLOCK}
api:
  reboot_timeout: 0s
{COMMON_TAIL}"""

CT2_EXTRA = """
mqtt:
  broker: "192.168.6.88"
  discovery: true
  on_message:
    - topic: "ct2/ble/send"
      then:
        - lambda: |-
            id(ct1_ble).send_hex(x);
bluetooth_proxy:
  active: false
"""

CT4_HEADER = f"""esphome:
  name: ct4
  friendly_name: CT4 Pro
  on_boot:
    priority: 600.0
    then:
      - light.turn_on: blue_led
      - light.turn_on: white_led
{ESP32_BLOCK}
{WIFI_BLOCK}
api:
  reboot_timeout: 0s
  on_client_connected:
    - script.stop: offline_flash
    - light.turn_off: white_led
    - light.turn_off: blue_led
  on_client_disconnected:
    - script.execute: offline_flash
ota:
  - platform: esphome
esp32_ble:
  io_capability: none
  enable_on_boot: true
bluetooth_proxy:
  active: true
  cache_services: true
globals:
  - id: do_factory_reset
    type: bool
    restore_value: no
    initial_value: 'false'
  - id: safe_mode_tap_count
    type: int
    restore_value: no
    initial_value: '0'
script:
  - id: offline_flash
    mode: restart
    then:
      - while:
          condition: {{ lambda: 'return true;' }}
          then: [light.toggle: white_led, delay: 500ms]
output:
  - platform: gpio
    id: blue_led_out
    pin: {{ number: GPIO27, inverted: true }}
  - platform: gpio
    id: white_led_out
    pin: {{ number: GPIO26, inverted: true }}
external_components:
  - source:
      type: local
      path: components
ble_gateway:
  id: ct1_ble
"""

GATEWAY_SENSOR = """  - platform: uptime
    name: "Gateway Uptime"
  - platform: internal_temperature
    name: "ESP32 Chip Temperature"
    unit_of_measurement: "°C"
    accuracy_decimals: 1
  - platform: wifi_signal
    name: "WiFi Signal dBm"
    id: wifi_signal_db
    update_interval: 60s
  - platform: copy
    source_id: wifi_signal_db
    name: "WiFi Signal Percent"
    filters:
      - lambda: return min(max(2*(x+100.0),0.0),100.0);
    unit_of_measurement: "%"
    icon: mdi:wifi-strength-4"""

GATEWAY_TEXT = """  - platform: wifi_info
    ip_address:
      name: "ESP IP Address"
    ssid:
      name: "ESP Connected SSID"
    bssid:
      name: "ESP Connected BSSID" """.rstrip()

GATEWAY_BUTTON = """  - platform: restart
    name: "Restart Gateway"
    icon: mdi:restart"""

CT4_LED_OUTPUTS = [
    "  - platform: binary\n    name: Blue LED\n    id: blue_led\n"
    "    output: blue_led_out\n    restore_mode: RESTORE_DEFAULT_OFF",
    "  - platform: binary\n    name: White LED\n    id: white_led\n"
    "    output: white_led_out\n    restore_mode: RESTORE_DEFAULT_OFF",
]

CT4_KEY_PINS = {"key1": "GPIO34", "key2": "GPIO35", "key3": "GPIO32", "key4": "GPIO33"}


# ============================================================
# Helpers
# ============================================================
def clean_hex(hex_str):
    return str(hex_str).strip().replace(" ", "").replace("0x", "").replace("0X", "").upper()


def get_english_name(dev_id):
    return dev_id.split(".")[-1].replace("_", " ").title()


def sid_of(dev):
    return dev["id"].replace(".", "_")


# ============================================================
# Load devices
# ============================================================
def load_devices(config_dir: Path):
    print(f"Scanning: {config_dir}")
    json_files = sorted(glob.glob(str(config_dir / "*.json")))
    if not json_files:
        print("No .json files found!")
        return None

    devices, used_ids = [], set()
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  ERROR in {Path(jf).name}: {e}")
            return None
        if "id" not in data:
            continue
        if data["id"] in used_ids:
            print(f"ERROR: Duplicate ID '{data['id']}' in {Path(jf).name}")
            return None
        used_ids.add(data["id"])
        data.setdefault("protocol", "8153")
        devices.append(data)
        print(f"  OK: {data['id']} (protocol: {data['protocol']})")
    return devices


# ============================================================
# 1. C++ device_table.cpp
# ============================================================
def generate_cpp(devices, out_path: Path):
    lines = [
        '#include "device_table.h"',
        "",
        "namespace esphome {",
        "namespace ble_gateway {",
        "",
        "void DeviceTable::load(std::vector<BLEDevice> &devices) {",
    ]
    for dev in devices:
        name = get_english_name(dev["id"])
        for kind in ("light", "fan"):
            if kind not in dev:
                continue
            tid = dev[kind]["id"]
            lines.append("")
            lines.append(f'    add_device(devices, "{tid}", "{kind}", "{name} {kind.title()}");')
            for act, pkts in dev[kind].get("actions", {}).items():
                pc = [clean_hex(p) for p in pkts if str(p).strip()]
                if not pc:
                    continue
                ps = ",\n        ".join(f'"{p}"' for p in pc)
                lines.append(f'    add_action(devices, "{tid}", "{act}", {{')
                lines.append(f"        {ps}")
                lines.append("    });")
    lines += [
        "",
        "}",
        "void DeviceTable::add_device(std::vector<BLEDevice> &d, const std::string &id, "
        "const std::string &type, const std::string &name) { BLEDevice device; device.id=id; "
        "device.type=type; device.name=name; d.push_back(device); }",
        "void DeviceTable::add_action(std::vector<BLEDevice> &d, const std::string &did, "
        "const std::string &action, std::vector<std::string> packets) { for(auto &device:d)"
        "{if(device.id==did){BLEAction act;act.name=action;act.packets=packets;"
        "device.actions[action]=act;return;}} }",
        "} // namespace ble_gateway",
        "} // namespace esphome",
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


# ============================================================
# 2. Entity lists
# ============================================================
def generate_entities(devices):
    sections = {
        "binary_sensor": [],
        "sensor": [GATEWAY_SENSOR],
        "text_sensor": [GATEWAY_TEXT],
        "button": [GATEWAY_BUTTON],
        "light": [],
        "fan": [],
    }
    for dev in devices:
        sid, name = sid_of(dev), get_english_name(dev["id"])
        if dev.get("mac"):
            sections["binary_sensor"] += [
                f'  - platform: template\n    id: {sid}_led_state\n'
                f'    name: "{name} LED"\n    device_class: light',
                f'  - platform: template\n    id: {sid}_fan_state\n'
                f'    name: "{name} Fan State"\n    device_class: running',
            ]
            sections["sensor"] += [
                f'  - platform: template\n    id: {sid}_brightness\n'
                f'    name: "{name} Brightness"\n    unit_of_measurement: "%"\n'
                f"    accuracy_decimals: 0",
                f'  - platform: template\n    id: {sid}_color_temp\n'
                f'    name: "{name} Color Temp"\n    unit_of_measurement: "K"\n'
                f"    accuracy_decimals: 0",
                f'  - platform: template\n    id: {sid}_fan_speed\n'
                f'    name: "{name} Fan Speed"\n    accuracy_decimals: 0',
                f'  - platform: template\n    id: {sid}_timer\n'
                f'    name: "{name} Timer"\n    unit_of_measurement: "min"\n'
                f"    accuracy_decimals: 0",
            ]
            sections["text_sensor"].append(
                f'  - platform: template\n    id: {sid}_fan_direction\n'
                f'    name: "{name} Fan Direction"'
            )
        if "light" in dev:
            sections["light"].append(
                f'  - platform: ble_light\n    id: {sid}_light_ctrl\n'
                f'    name: "{name} Light"\n'
                f'    ble_device_id: "{dev["light"]["id"]}"\n    gateway: ct1_ble'
            )
        if "fan" in dev:
            sections["fan"].append(
                f'  - platform: ble_fan\n    id: {sid}_fan_ctrl\n'
                f'    name: "{name} Fan"\n'
                f'    ble_device_id: "{dev["fan"]["id"]}"\n    gateway: ct1_ble'
            )
    return sections


# ============================================================
# 3. BLE tracker lambda
# ============================================================
_PUBLISH_TMPL = """
                    if (mac == "{mac}") {{
                        id({sid}_led_state).publish_state({led});
                        id({sid}_brightness).publish_state({brt});
                        id({sid}_color_temp).publish_state({ctemp});
                        id({sid}_fan_state).publish_state({fan});
                        id({sid}_fan_speed).publish_state({speed});
                        id({sid}_fan_direction).publish_state({dir});
                        id({sid}_timer).publish_state({timer});
                    }}
"""

def _publish_block(dev, *, led, brt, ctemp, fan, speed, dir_, timer):
    return _PUBLISH_TMPL.format(
        mac=dev["mac"].lower(), sid=sid_of(dev),
        led=led, brt=brt, ctemp=ctemp, fan=fan, speed=speed, dir=dir_, timer=timer,
    )


def generate_tracker(devices):
    dev_8153 = [d for d in devices if d["protocol"] == "8153"]
    dev_134d = [d for d in devices if d["protocol"] == "134D"]

    parts = ["""esp32_ble_tracker:
  scan_parameters:
    interval: 320ms
    window: 30ms
    active: false
  on_ble_advertise:
    - then:
        - lambda: |-
            auto datas = x.get_manufacturer_datas();
            for (auto &data : datas) {
                auto &raw = data.data;
                if (raw.size() < 20) continue;
"""]

    if dev_8153:
        parts.append("""
                // === Protocol 8153 ===
                if (raw[0] == 0x81 && raw[1] == 0x53) {
                    std::string he = "";
                    for (uint8_t b : raw) { char buf[3]; sprintf(buf, "%02x", b); he += buf; }
                    if (he.length() < 40) continue;
                    std::string mac_raw = he.substr(6, 12);
                    std::string mac = "";
                    for (int i = 10; i >= 0; i -= 2) { mac += mac_raw.substr(i, 2); if (i > 0) mac += ":"; }
                    int mode = strtol(he.substr(22, 2).c_str(), nullptr, 16);
                    bool led_on = (mode & 0x01) != 0;
                    bool fan_on = !(mode == 0x10 || mode == 0x11);
                    bool fan_reverse = (mode & 0x20) != 0;
                    float brightness_pct = (strtol(he.substr(28, 2).c_str(), nullptr, 16) / 255.0f) * 100.0f;
                    float color_pct = strtol(he.substr(30, 2).c_str(), nullptr, 16) / 255.0f;
                    float color_kelvin = 2700.0f + (6500.0f - 2700.0f) * color_pct;
                    int timer_min = strtol(he.substr(32, 4).c_str(), nullptr, 16);
                    int fan_speed = fan_on ? (strtol(he.substr(36, 2).c_str(), nullptr, 16) + 1) : 0;
                    std::string fan_dir_str = fan_on ? (fan_reverse ? "Reverse" : "Forward") : "Off";
""")
        for dev in dev_8153:
            parts.append(_publish_block(
                dev, led="led_on", brt="brightness_pct", ctemp="color_kelvin",
                fan="fan_on", speed="fan_speed", dir_="fan_dir_str", timer="timer_min",
            ))
        parts.append("                    break;\n                }\n")

    if dev_134d:
        parts.append("""
                // === Protocol 134D ===
                if (raw[0] == 0x21) {
                    char mac_buf[18];
                    sprintf(mac_buf, "%02x:%02x:%02x:%02x:%02x:%02x", raw[7], raw[6], raw[5], raw[4], raw[3], raw[2]);
                    std::string mac(mac_buf);
                    
                    bool power_on = (raw[9] == 0x01);
                    uint16_t brt_raw = (raw[14] << 8) | raw[15];
                    int brt_pct = (brt_raw == 0xFFFF) ? 100 : (int)(brt_raw / 655.35);
                    
                    uint8_t state_byte = raw[18];
                    bool fan_running = (state_byte == 0x13 || state_byte == 0x03);
                    uint8_t fan_gear = raw[19];
                    int fan_speed = fan_running ? (fan_gear + 1) : 0;
                    std::string fan_dir_str = fan_running ? "Forward" : "Off";
""")
        for dev in dev_134d:
            parts.append(_publish_block(
                dev, led="power_on", brt="brt_pct", ctemp="0",
                fan="fan_running", speed="fan_speed", dir_="fan_dir_str", timer="0",
            ))
        parts.append("                    break;\n                }\n")

    parts.append("            }\n")
    return "".join(parts)


# ============================================================
# 4. YAML writers
# ============================================================
_SECTION_ORDER = ("binary_sensor", "sensor", "text_sensor", "button", "light", "fan")

def _render_sections(sections):
    out = []
    for key in _SECTION_ORDER:
        items = sections.get(key)
        if items:
            out.append(f"{key}:\n" + "\n".join(items) + "\n\n")
    return "".join(out)


def write_yaml(path: Path, header, sections, tracker, extra=""):
    body = header + _render_sections(sections) + extra + "\n" + tracker
    path.write_text(body)


def _build_ct4_keys():
    """Generate 4 GPIO key blocks. key1 has special long-press + double-click, others share the simple pattern."""
    common_click_tmpl = (
        "  - platform: gpio\n"
        "    id: {kid}\n    name: {KID}\n"
        "    pin: {{ number: {pin}, inverted: true }}\n"
        "    filters: [delayed_on: 20ms, delayed_off: 20ms]\n"
        "    on_multi_click:\n"
        "      - timing: [ON for at least 1.5s]\n"
        "        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, "
        'homeassistant.event: {{ event: esphome.gateway_key, data: {{ key: "{kid}", mode: "long" }} }}]\n'
        "      - timing: [ON for at most 0.5s, OFF for at least 0.3s]\n"
        "        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, "
        'homeassistant.event: {{ event: esphome.gateway_key, data: {{ key: "{kid}", mode: "single" }} }}]'
    )

    key1_block = (
        "\n  - platform: gpio\n"
        "    id: key1\n    name: KEY1\n"
        f"    pin: {{ number: {CT4_KEY_PINS['key1']}, inverted: true }}\n"
        "    filters: [delayed_on: 20ms, delayed_off: 20ms]\n"
        "    on_multi_click:\n"
        "      - timing: [ON for at least 8s]\n"
        "        then:\n"
        "          - if: { condition: { binary_sensor.is_on: key4 }, then: [delay: 500ms, "
        "if: { condition: { binary_sensor.is_on: key4 }, then: [lambda: 'id(do_factory_reset)=true;', "
        "repeat: { count: 5, then: [light.toggle: white_led, delay: 100ms] }, "
        "lambda: 'App.reboot();'] }]}\n"
        "      - timing: [ON for at least 1.5s]\n"
        "        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, "
        'homeassistant.event: { event: esphome.gateway_key, data: { key: "key1", mode: "long" } }]\n'
        "      - timing: [ON for at most 0.5s, OFF for at most 0.3s, ON for at most 0.5s, "
        "OFF for at least 0.3s]\n"
        "        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, "
        'homeassistant.event: { event: esphome.gateway_key, data: { key: "key1", mode: "double" } }]\n'
        "      - timing: [ON for at most 0.5s, OFF for at least 0.3s]\n"
        "        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, "
        'homeassistant.event: { event: esphome.gateway_key, data: { key: "key1", mode: "single" } }]'
    )

    blocks = [key1_block]
    for kid in ("key2", "key3", "key4"):
        blocks.append(common_click_tmpl.format(kid=kid, KID=kid.upper(), pin=CT4_KEY_PINS[kid]))
    return "\n".join(blocks) + "\n"


def write_ct4(path: Path, sections, tracker):
    keys_yaml = _build_ct4_keys()
    # Merge CT4 key binary_sensor into the existing binary_sensor section
    bs_items = sections["binary_sensor"]
    merged_bs = ("\n".join(bs_items) + keys_yaml) if bs_items else keys_yaml
    # Prepend LED lights to the light section
    ly_items = CT4_LED_OUTPUTS + sections["light"]

    ct4_sections = {
        "binary_sensor": [merged_bs],
        "sensor": sections["sensor"],
        "text_sensor": sections["text_sensor"],
        "button": sections["button"],
        "light": ly_items,
        "fan": sections["fan"],
    }
    path.write_text(CT4_HEADER + _render_sections(ct4_sections) + tracker)


# ============================================================
# Main
# ============================================================
def generate_all(config_dir: Path, base_dir: Path):
    devices = load_devices(config_dir)
    if devices is None:
        return

    generate_cpp(devices, base_dir / "components" / "ble_gateway" / "device_table.cpp")

    sections = generate_entities(devices)
    tracker = generate_tracker(devices)

    write_yaml(base_dir / "ct1.yaml",
               BASE_TEMPLATE.format(name="ct1", fn="CT1 Lite"), sections, tracker)
    write_yaml(base_dir / "ct2.yaml",
               BASE_TEMPLATE.format(name="ct2", fn="CT2 Full"), sections, tracker,
               extra=CT2_EXTRA)
    write_yaml(base_dir / "ct3.yaml",
               BASE_TEMPLATE.format(name="ct3", fn="CT3 Custom"), sections, tracker)
    write_ct4(base_dir / "ct4.yaml", sections, tracker)

    print("All files generated successfully.")


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    cfg = base / "devices_config"
    if not cfg.exists():
        print(f"Error: {cfg} not found.")
        raise SystemExit(1)
    generate_all(cfg, base)
