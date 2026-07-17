import json
import os
import glob
from pathlib import Path

# ==============================================================================
# 🔥 核心配置区：在这里修改基础名字！
# ==============================================================================
PROJECT_PREFIX = "ct"  
# ==============================================================================

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

    devices, used_dev_ids = [], set()
    used_light_ids, used_fan_ids = set(), set()

    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  ERROR in {os.path.basename(jf)}: {e}")
            return
        
        if "id" not in data: continue
        dev_id = data["id"]
        if dev_id in used_dev_ids:
            print(f"❌ FATAL: Duplicate device ID '{dev_id}' in {os.path.basename(jf)}")
            return
        used_dev_ids.add(dev_id)
        
        if "light" in data:
            lid = data["light"].get("id")
            if lid and lid in used_light_ids:
                print(f"❌ FATAL: Duplicate light ID '{lid}' in {os.path.basename(jf)}")
                return
            if lid: used_light_ids.add(lid)
                
        if "fan" in data:
            fid = data["fan"].get("id")
            if fid and fid in used_fan_ids:
                print(f"❌ FATAL: Duplicate fan ID '{fid}' in {os.path.basename(jf)}")
                return
            if fid: used_fan_ids.add(fid)

        data.setdefault("protocol", "8153")
        devices.append(data)
        print(f"  OK: {dev_id} (protocol: {data['protocol']})")

    # 1. 生成全局 C++ device_table.cpp
    cpp = ['#include "device_table.h"', '#include "esphome/core/log.h"', "", "namespace esphome {", "namespace ble_gateway {", "", "static const char *TAG = \"device_table\";", "", "void DeviceTable::load(std::vector<BLEDevice> &devices) {"]
    for dev in devices:
        name = get_english_name(dev["id"])
        for kind in ("light", "fan"):
            if kind not in dev: continue
            tid = dev[kind]["id"]
            cpp.append(f'    add_device(devices, "{tid}", "{kind}", "{name} {kind.title()}");')
            for act, pkts in dev[kind].get("actions", {}).items():
                pc = [clean_hex(p) for p in pkts if str(p).strip()]
                if not pc: continue
                ps = ",\n        ".join(f'"{p}"' for p in pc)
                cpp.append(f'    add_action(devices, "{tid}", "{act}", {{\n        {ps}\n    }});')
    
    cpp += [
        "", "}",
        "void DeviceTable::add_device(std::vector<BLEDevice> &d, const std::string &id, const std::string &type, const std::string &name) { BLEDevice device; device.id=id; device.type=type; device.name=name; d.push_back(std::move(device)); }",
        "void DeviceTable::add_action(std::vector<BLEDevice> &d, const std::string &did, const std::string &action, std::vector<std::string> packets) { for(auto &device:d){if(device.id==did){BLEAction act;act.name=action;act.packets=std::move(packets);device.actions.emplace(action, std::move(act));return;}} ESP_LOGE(TAG, \"Device ID not found: %s\", did.c_str()); }",
        "} // namespace ble_gateway", "} // namespace esphome", ""
    ]
    (base_dir / "components" / "ble_gateway" / "device_table.cpp").write_text("\n".join(cpp))

    # 2. 生成全局实体列表
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

    # 3. 生成全局 BLE Tracker
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
                        id({sid}_led_state).publish_state(led_on); id({sid}_brightness).publish_state(brightness_pct);
                        id({sid}_color_temp).publish_state(color_kelvin); id({sid}_fan_state).publish_state(fan_on);
                        id({sid}_fan_speed).publish_state(fan_speed); id({sid}_fan_direction).publish_state(fan_dir_str);
                        id({sid}_timer).publish_state(timer_min);
                    }}
"""
        tracker += "                    break;\n                }\n"

    if dev_134d:
        tracker += """
                // === Protocol 134D ===
"""
        for dev in dev_134d:
            sid = dev["id"].replace(".", "_")
            mac_bytes = dev["mac"].split(":")
            mac_array = "{" + ", ".join([f"0x{b}" for b in reversed(mac_bytes)]) + "}"
            tracker += f"""
                uint8_t target_mac_{sid}[6] = {mac_array};
                for (int i = 2; i <= (int)raw.size() - 6; i++) {{
                    if (memcmp(&raw[i], target_mac_{sid}, 6) == 0) {{
                        bool power_on = (raw[i + 7] == 0x01);
                        uint16_t brt_raw_val = (raw[i + 12] << 8) | raw[i + 13];
                        int brt_pct = (brt_raw_val == 0xFFFF) ? 100 : (int)(brt_raw_val / 655.35);
                        uint8_t state_byte = raw[i + 14];
                        bool fan_running = (state_byte == 0x13 || state_byte == 0x03);
                        uint8_t fan_gear = raw[i + 15];
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

    # 4. 基础模板 (统一满血蓝牙代理)
    base_template = f"""esphome:
  name: {{name}}
  friendly_name: {{fn}}
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
    ssid: "{{name}} Fallback"
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

esp32_ble:
  io_capability: none
  enable_on_boot: true
bluetooth_proxy:
  active: true
  cache_services: true
"""

    # 🔥 核心修复：使用标准展开的 YAML 格式，彻底消灭 {} 和转义问题
    pro_keys_yaml = """  - platform: gpio
    id: key1
    name: KEY1
    pin: 
      number: GPIO34
      inverted: true
    filters: 
      - delayed_on: 20ms
      - delayed_off: 20ms
    on_multi_click:
      - timing: 
          - ON for at least 8s
        then:
          - if:
              condition:
                binary_sensor.is_on: key4
              then:
                - delay: 500ms
                - if:
                    condition:
                      binary_sensor.is_on: key4
                    then:
                      - lambda: 'id(do_factory_reset)=true;'
                      - repeat:
                          count: 5
                          then:
                            - light.toggle: white_led
                            - delay: 100ms
                      - lambda: 'App.reboot();'
      - timing: 
          - ON for at least 1.5s
        then: 
          - light.turn_on: blue_led
          - delay: 200ms
          - light.turn_off: blue_led
          - homeassistant.event: 
              event: esphome.gateway_key
              data: 
                key: "key1"
                mode: "long"
      - timing: 
          - ON for at most 0.5s
          - OFF for at most 0.3s
          - ON for at most 0.5s
          - OFF for at least 0.3s
        then: 
          - light.turn_on: blue_led
          - delay: 200ms
          - light.turn_off: blue_led
          - homeassistant.event: 
              event: esphome.gateway_key
              data: 
                key: "key1"
                mode: "double"
      - timing: 
          - ON for at most 0.5s
          - OFF for at least 0.3s
        then: 
          - light.turn_on: blue_led
          - delay: 200ms
          - light.turn_off: blue_led
          - homeassistant.event: 
              event: esphome.gateway_key
              data: 
                key: "key1"
                mode: "single"
  - platform: gpio
    id: key2
    name: KEY2
    pin: 
      number: GPIO35
      inverted: true
    filters: 
      - delayed_on: 20ms
      - delayed_off: 20ms
    on_multi_click:
      - timing: 
          - ON for at least 1.5s
        then: 
          - light.turn_on: blue_led
          - delay: 200ms
          - light.turn_off: blue_led
          - homeassistant.event: 
              event: esphome.gateway_key
              data: 
                key: "key2"
                mode: "long"
      - timing: 
          - ON for at most 0.5s
          - OFF for at least 0.3s
        then: 
          - light.turn_on: blue_led
          - delay: 200ms
          - light.turn_off: blue_led
          - homeassistant.event: 
              event: esphome.gateway_key
              data: 
                key: "key2"
                mode: "single"
  - platform: gpio
    id: key3
    name: KEY3
    pin: 
      number: GPIO32
      inverted: true
    filters: 
      - delayed_on: 20ms
      - delayed_off: 20ms
    on_multi_click:
      - timing: 
          - ON for at least 1.5s
        then: 
          - light.turn_on: blue_led
          - delay: 200ms
          - light.turn_off: blue_led
          - homeassistant.event: 
              event: esphome.gateway_key
              data: 
                key: "key3"
                mode: "long"
      - timing: 
          - ON for at most 0.5s
          - OFF for at least 0.3s
        then: 
          - light.turn_on: blue_led
          - delay: 200ms
          - light.turn_off: blue_led
          - homeassistant.event: 
              event: esphome.gateway_key
              data: 
                key: "key3"
                mode: "single"
  - platform: gpio
    id: key4
    name: KEY4
    pin: 
      number: GPIO33
      inverted: true
    filters: 
      - delayed_on: 20ms
      - delayed_off: 20ms
    on_multi_click:
      - timing: 
          - ON for at least 1.5s
        then: 
          - light.turn_on: blue_led
          - delay: 200ms
          - light.turn_off: blue_led
          - homeassistant.event: 
              event: esphome.gateway_key
              data: 
                key: "key4"
                mode: "long"
      - timing: 
          - ON for at most 0.5s
          - OFF for at least 0.3s
        then: 
          - light.turn_on: blue_led
          - delay: 200ms
          - light.turn_off: blue_led
          - homeassistant.event: 
              event: esphome.gateway_key
              data: 
                key: "key4"
                mode: "single"
"""

    pro_leds_yaml = """  - platform: binary
    name: Blue LED
    id: blue_led
    output: blue_led_out
    restore_mode: RESTORE_DEFAULT_OFF
  - platform: binary
    name: White LED
    id: white_led
    output: white_led_out
    restore_mode: RESTORE_DEFAULT_OFF
"""

    pro_extras_yaml = """
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
          condition: 
            lambda: 'return true;'
          then: 
            - light.toggle: white_led
            - delay: 500ms
output:
  - platform: gpio
    id: blue_led_out
    pin: 
      number: GPIO27
      inverted: true
  - platform: gpio
    id: white_led_out
    pin: 
      number: GPIO26
      inverted: true
"""

    # 🔥 核心修复：预先生成全局的 binary_sensor 和 light 字符串，确保顶层键唯一
    bs_content = ""
    if sections["binary_sensor"]:
        bs_content = "binary_sensor:\n" + "\n".join(sections["binary_sensor"]) + "\n"

    light_content = ""
    if sections["light"]:
        light_content = "light:\n" + "\n".join(sections["light"]) + "\n"

    def write_yaml(filename, name, fn, extra_yaml="", is_pro=False):
        content = base_template.format(name=name, fn=fn)
        
        # 1. binary_sensor (合并 Pro 按键)
        if bs_content:
            content += bs_content
            if is_pro:
                content += pro_keys_yaml
            content += "\n"
            
        # 2. 常规 sections
        for key in ("sensor", "text_sensor", "button", "fan"):
            if sections[key]:
                content += f"{key}:\n" + "\n".join(sections[key]) + "\n\n"
                
        # 3. light (合并 Pro LED)
        if light_content:
            content += light_content
            if is_pro:
                content += pro_leds_yaml
            content += "\n"
            
        # 4. Pro 专属 globals/script/output
        if is_pro:
            content += pro_extras_yaml + "\n"
            
        # 5. 额外配置 (如 MQTT) 和 Tracker
        content += extra_yaml + "\n" + tracker
        (base_dir / filename).write_text(content)

    # 6. 生成 4 个固件
    prefix = PROJECT_PREFIX
    
    write_yaml(f"{prefix}1.yaml", f"{prefix}1", f"{prefix}1 Lite")
    
    # 🔥 使用 f-string 直接替换，避免 .format() 崩溃
    mqtt_extra = f"""mqtt:
  broker: "192.168.6.88"
  discovery: true
  on_message:
    - topic: "{prefix}2/ble/send"
      then:
        - lambda: |-
            id(ct1_ble).send_hex(x);
"""
    write_yaml(f"{prefix}2.yaml", f"{prefix}2", f"{prefix}2 Full", mqtt_extra)
    
    write_yaml(f"{prefix}3.yaml", f"{prefix}3", f"{prefix}3 Custom")
    
    write_yaml(f"{prefix}4.yaml", f"{prefix}4", f"{prefix}4 Pro", is_pro=True)

    print(f"✅ Successfully generated {prefix}1~4.yaml with unified Bluetooth Proxy and stable YAML structure.")

if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    cfg = base / "devices_config"
    if not cfg.exists():
        print(f"Error: {cfg} not found.")
        raise SystemExit(1)
    generate_all(cfg, base)
