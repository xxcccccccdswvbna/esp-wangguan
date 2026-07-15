import json
import os
import glob
from pathlib import Path

def clean_hex(hex_str):
    return str(hex_str).strip().replace(" ", "").replace("0x", "").replace("0X", "").upper()

def get_english_name(dev_id):
    return dev_id.split(".")[-1].replace("_", " ").title()

def generate_all(config_dir: Path, base_dir: Path):
    print(f"Scanning: {config_dir}")
    json_files = sorted(glob.glob(str(config_dir / "*.json")))
    if not json_files:
        print("No .json files found!")
        return

    devices, used_ids = [], set()
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  ERROR in {os.path.basename(jf)}: {e}")
            return
        if "id" not in data:
            continue
        if data["id"] in used_ids:
            print(f"ERROR: Duplicate ID '{data['id']}' in {os.path.basename(jf)}")
            return
        used_ids.add(data["id"])
        data.setdefault("protocol", "8153")
        devices.append(data)
        print(f"  OK: {data['id']} (protocol: {data['protocol']})")

    # ========== 1. C++ device_table.cpp ==========
    cpp = ['#include "device_table.h"', "", "namespace esphome {", "namespace ble_gateway {", "", "void DeviceTable::load(std::vector<BLEDevice> &devices) {"]
    for dev in devices:
        name = get_english_name(dev["id"])
        for kind in ("light", "fan"):
            if kind not in dev:
                continue
            tid = dev[kind]["id"]
            cpp.append("")
            cpp.append(f'    add_device(devices, "{tid}", "{kind}", "{name} {kind.title()}");')
            for act, pkts in dev[kind].get("actions", {}).items():
                pc = [clean_hex(p) for p in pkts if str(p).strip()]
                if not pc:
                    continue
                ps = ",\n        ".join(f'"{p}"' for p in pc)
                cpp.append(f'    add_action(devices, "{tid}", "{act}", {{')
                cpp.append(f"        {ps}")
                cpp.append("    });")
    
    # 🔥 核心修复：匹配 device_table.h 中的 const std::string& 签名，并加入 std::move 优化
    cpp += [
        "", "}",
        "void DeviceTable::add_device(std::vector<BLEDevice> &d, const std::string &id, const std::string &type, const std::string &name) { BLEDevice device; device.id=id; device.type=type; device.name=name; d.push_back(std::move(device)); }",
        "void DeviceTable::add_action(std::vector<BLEDevice> &d, const std::string &did, const std::string &action, std::vector<std::string> packets) { for(auto &device:d){if(device.id==did){BLEAction act;act.name=action;act.packets=std::move(packets);device.actions.emplace(action, std::move(act));return;}} }",
        "} // namespace ble_gateway", "} // namespace esphome", ""
    ]
    (base_dir / "components" / "ble_gateway" / "device_table.cpp").write_text("\n".join(cpp))

    # ========== 2. 实体列表 ==========
    sections = {"binary_sensor": [], "sensor": [], "text_sensor": [], "button": [], "light": [], "fan": []}
    sections["sensor"].append('  - platform: uptime\n    name: "Gateway Uptime"\n  - platform: internal_temperature\n    name: "ESP32 Chip Temperature"\n    unit_of_measurement: "°C"\n    accuracy_decimals: 1\n  - platform: wifi_signal\n    name: "WiFi Signal dBm"\n    id: wifi_signal_db\n    update_interval: 60s\n  - platform: copy\n    source_id: wifi_signal_db\n    name: "WiFi Signal Percent"\n    filters:\n      - lambda: return min(max(2*(x+100.0),0.0),100.0);\n    unit_of_measurement: "%"\n    icon: mdi:wifi-strength-4')
    sections["text_sensor"].append('  - platform: wifi_info\n    ip_address:\n      name: "ESP IP Address"\n    ssid:\n      name: "ESP Connected SSID"\n    bssid:\n      name: "ESP Connected BSSID"')
    sections["button"].append('  - platform: restart\n    name: "Restart Gateway"\n    icon: mdi:restart')

    for dev in devices:
        sid, name = dev["id"].replace(".", "_"), get_english_name(dev["id"])
        if dev.get("mac"):
            sections["binary_sensor"] += [f'  - platform: template\n    id: {sid}_led_state\n    name: "{name} LED"\n    device_class: light', f'  - platform: template\n    id: {sid}_fan_state\n    name: "{name} Fan State"\n    device_class: running']
            sections["sensor"] += [f'  - platform: template\n    id: {sid}_brightness\n    name: "{name} Brightness"\n    unit_of_measurement: "%"\n    accuracy_decimals: 0', f'  - platform: template\n    id: {sid}_color_temp\n    name: "{name} Color Temp"\n    unit_of_measurement: "K"\n    accuracy_decimals: 0', f'  - platform: template\n    id: {sid}_fan_speed\n    name: "{name} Fan Speed"\n    accuracy_decimals: 0', f'  - platform: template\n    id: {sid}_timer\n    name: "{name} Timer"\n    unit_of_measurement: "min"\n    accuracy_decimals: 0']
            sections["text_sensor"].append(f'  - platform: template\n    id: {sid}_fan_direction\n    name: "{name} Fan Direction"')
        if "light" in dev:
            sections["light"].append(f'  - platform: ble_light\n    id: {sid}_light_ctrl\n    name: "{name} Light"\n    ble_device_id: "{dev["light"]["id"]}"\n    gateway: ct1_ble')
        if "fan" in dev:
            sections["fan"].append(f'  - platform: ble_fan\n    id: {sid}_fan_ctrl\n    name: "{name} Fan"\n    ble_device_id: "{dev["fan"]["id"]}"\n    gateway: ct1_ble')

    # ========== 3. BLE Tracker (8153 + 134D 动态 MAC 搜索) ==========
    dev_8153 = [d for d in devices if d["protocol"] == "8153"]
    dev_134d = [d for d in devices if d["protocol"] == "134D"]

    tracker = """esp32_ble_tracker:
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
"""
    if dev_8153:
        tracker += """
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
"""
        for dev in dev_8153:
            sid = dev["id"].replace(".", "_")
            tracker += f"""
                    if (mac == "{dev['mac'].lower()}") {{
                        id({sid}_led_state).publish_state(led_on);
                        id({sid}_brightness).publish_state(brightness_pct);
                        id({sid}_color_temp).publish_state(color_kelvin);
                        id({sid}_fan_state).publish_state(fan_on);
                        id({sid}_fan_speed).publish_state(fan_speed);
                        id({sid}_fan_direction).publish_state(fan_dir_str);
                        id({sid}_timer).publish_state(timer_min);
                    }}
"""
        tracker += "                    break;\n                }\n"

    if dev_134d:
        tracker += """
                // === Protocol 134D (动态 MAC 搜索) ===
"""
        for dev in dev_134d:
            sid = dev["id"].replace(".", "_")
            mac_bytes = dev["mac"].split(":")
            mac_array = "{" + ", ".join([f"0x{b}" for b in reversed(mac_bytes)]) + "}"
            tracker += f"""
                uint8_t target_mac_{sid}[6] = {mac_array};
                for (int i = 5; i <= (int)raw.size() - 6; i++) {{
                    if (memcmp(&raw[i], target_mac_{sid}, 6) == 0) {{
                        uint8_t switch_byte1 = raw[i + 6];
                        uint8_t switch_byte2 = raw[i + 7];
                        bool power_on = (switch_byte1 == 0x01 || switch_byte2 == 0x01);
                        uint16_t brt_raw_val = (raw[i + 11] << 8) | raw[i + 12];
                        int brt_pct = (brt_raw_val == 0xFFFF) ? 100 : (int)(brt_raw_val / 655.35);
                        bool fan_running = false;
                        uint8_t fan_gear = 0;
                        for (int j = i + 13; j < (int)raw.size() - 1; j++) {{
                            if (raw[j] == 0x13 || raw[j] == 0x03) {{ fan_running = true; fan_gear = raw[j+1]; break; }}
                            else if (raw[j] == 0x02 || raw[j] == 0x12) {{ fan_running = false; fan_gear = 0; break; }}
                        }}
                        int fan_speed = fan_running ? (fan_gear + 1) : 0;
                        std::string fan_dir_str = fan_running ? "Forward" : "Off";
                        id({sid}_led_state).publish_state(power_on);
                        id({sid}_brightness).publish_state(brt_pct);
                        id({sid}_fan_state).publish_state(fan_running);
                        id({sid}_fan_speed).publish_state(fan_speed);
                        id({sid}_fan_direction).publish_state(fan_dir_str);
                        id({sid}_color_temp).publish_state(0);
                        id({sid}_timer).publish_state(0);
                        break;
                    }}
                }}
"""
    tracker += "            }\n"

    # ========== 4. 写入 CT1, CT2, CT3 ==========
    base = """esphome:
  name: {name}
  friendly_name: {fn}
esp32:
  board: esp32dev
  flash_size: 4MB
  framework:
    type: esp-idf
    sdkconfig_options:
      CONFIG_FREERTOS_UNICORE: y
      CONFIG_BT_ENABLED: y
      CONFIG_BT_BLE_ENABLED: y
logger:
  baud_rate: 0
wifi:
  ssid: "CC"
  password: "chen1122"
  fast_connect: true
  power_save_mode: none
  ap:
    ssid: "CT1 Fallback"
    password: "12345678"
captive_portal:
web_server:
api:
  reboot_timeout: 0s
ota:
  - platform: esphome
external_components:
  - source:
      type: local
      path: components
ble_gateway:
  id: ct1_ble
"""
    def write(fn, hdr, extra=""):
        c = hdr
        for key in ("binary_sensor", "sensor", "text_sensor", "button", "light", "fan"):
            if sections[key]:
                c += f"{key}:\n" + "\n".join(sections[key]) + "\n\n"
        c += extra + "\n" + tracker
        (base_dir / fn).write_text(c)

    write("ct1.yaml", base.format(name="ct1", fn="CT1 Lite"))
    write("ct2.yaml", base.format(name="ct2", fn="CT2 Full"), extra='\nmqtt:\n  broker: "192.168.6.88"\n  discovery: true\n  on_message:\n    - topic: "ct2/ble/send"\n      then:\n        - lambda: |-\n            id(ct1_ble).send_hex(x);\nbluetooth_proxy:\n  active: false\n')
    write("ct3.yaml", base.format(name="ct3", fn="CT3 Custom"))

    # ========== 5. 完整写入 CT4 (Pro 专属版，绝对无省略) ==========
    ct4_header = """esphome:
  name: ct4
  friendly_name: CT4 Pro
  on_boot:
    priority: 600.0
    then:
      - light.turn_on: blue_led
      - light.turn_on: white_led
esp32:
  board: esp32dev
  flash_size: 4MB
  framework:
    type: esp-idf
    sdkconfig_options:
      CONFIG_FREERTOS_UNICORE: y
      CONFIG_BT_ENABLED: y
      CONFIG_BT_BLE_ENABLED: y
logger:
  baud_rate: 0
wifi:
  ssid: "CC"
  password: "chen1122"
  fast_connect: true
  power_save_mode: none
  ap:
    ssid: "CT1 Fallback"
    password: "12345678"
captive_portal:
web_server:
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
          condition: { lambda: 'return true;' }
          then: [light.toggle: white_led, delay: 500ms]
output:
  - platform: gpio
    id: blue_led_out
    pin: { number: GPIO27, inverted: true }
  - platform: gpio
    id: white_led_out
    pin: { number: GPIO26, inverted: true }
external_components:
  - source:
      type: local
      path: components
ble_gateway:
  id: ct1_ble
"""
    
    ct4_leds = [
        '  - platform: binary\n    name: Blue LED\n    id: blue_led\n    output: blue_led_out\n    restore_mode: RESTORE_DEFAULT_OFF',
        '  - platform: binary\n    name: White LED\n    id: white_led\n    output: white_led_out\n    restore_mode: RESTORE_DEFAULT_OFF'
    ]
    
    ct4_keys = """
  - platform: gpio
    id: key1
    name: KEY1
    pin: { number: GPIO34, inverted: true }
    filters: [delayed_on: 20ms, delayed_off: 20ms]
    on_multi_click:
      - timing: [ON for at least 8s]
        then:
          - if: { condition: { binary_sensor.is_on: key4 }, then: [delay: 500ms, if: { condition: { binary_sensor.is_on: key4 }, then: [lambda: 'id(do_factory_reset)=true;', repeat: { count: 5, then: [light.toggle: white_led, delay: 100ms] }, lambda: 'App.reboot();'] }]}
      - timing: [ON for at least 1.5s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key1", mode: "long" } }]
      - timing: [ON for at most 0.5s, OFF for at most 0.3s, ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key1", mode: "double" } }]
      - timing: [ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key1", mode: "single" } }]
  - platform: gpio
    id: key2
    name: KEY2
    pin: { number: GPIO35, inverted: true }
    filters: [delayed_on: 20ms, delayed_off: 20ms]
    on_multi_click:
      - timing: [ON for at least 1.5s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key2", mode: "long" } }]
      - timing: [ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key2", mode: "single" } }]
  - platform: gpio
    id: key3
    name: KEY3
    pin: { number: GPIO32, inverted: true }
    filters: [delayed_on: 20ms, delayed_off: 20ms]
    on_multi_click:
      - timing: [ON for at least 1.5s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key3", mode: "long" } }]
      - timing: [ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key3", mode: "single" } }]
  - platform: gpio
    id: key4
    name: KEY4
    pin: { number: GPIO33, inverted: true }
    filters: [delayed_on: 20ms, delayed_off: 20ms]
    on_multi_click:
      - timing: [ON for at least 1.5s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key4", mode: "long" } }]
      - timing: [ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key4", mode: "single" } }]
"""

    c4 = ct4_header
    bs_content = "\n".join(sections["binary_sensor"]) + ct4_keys if sections["binary_sensor"] else ct4_keys
    c4 += f"binary_sensor:\n{bs_content}\n\n"
    if sections["sensor"]: c4 += "sensor:\n" + "\n".join(sections["sensor"]) + "\n\n"
    if sections["text_sensor"]: c4 += "text_sensor:\n" + "\n".join(sections["text_sensor"]) + "\n\n"
    if sections["button"]: c4 += "button:\n" + "\n".join(sections["button"]) + "\n\n"
    
    all_lights = ct4_leds + sections["light"]
    if all_lights: c4 += "light:\n" + "\n".join(all_lights) + "\n\n"
    if sections["fan"]: c4 += "fan:\n" + "\n".join(sections["fan"]) + "\n\n"
    c4 += tracker
    
    (base_dir / "ct4.yaml").write_text(c4)

    print("All 4 YAML files and C++ generated successfully.")

if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    cfg = base / "devices_config"
    if not cfg.exists():
        print(f"Error: {cfg} not found.")
        raise SystemExit(1)
    generate_all(cfg, base)