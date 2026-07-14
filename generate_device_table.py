import json
import os
import glob

def clean_hex(hex_str):
    hex_str = str(hex_str).strip().replace(" ", "").replace("0x", "").replace("0X", "")
    return hex_str.upper()

def get_english_name(dev_id):
    raw_name = dev_id.split('.')[-1]
    return raw_name.replace('_', ' ').title()

def generate_all(config_dir, base_dir):
    print(f"📂 Scanning config directory: {config_dir}")
    json_files = sorted(glob.glob(os.path.join(config_dir, "*.json")))
    
    if not json_files:
        print("⚠️ Warning: No .json files found!")
        return

    devices = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'id' in data:
                    devices.append(data)
                    print(f"  ✅ Loaded: {data['id']}")
        except json.JSONDecodeError as e:
            print(f"  ❌ Error in {os.path.basename(json_file)}: {e}")
            return

    print(f"🚀 Generating code for {len(devices)} devices...")

    # ==========================================
    # 1. 生成 C++ device_table.cpp (所有版本共用)
    # ==========================================
    cpp_code = """#include "device_table.h"

namespace esphome {
namespace ble_gateway {

void DeviceTable::load(std::vector<BLEDevice> &devices) {
"""
    for dev in devices:
        dev_name = get_english_name(dev['id'])
        if 'light' in dev:
            light_id = dev['light']['id']
            cpp_code += f"\n    add_device(devices, \"{light_id}\", \"light\", \"{dev_name} Light\");\n"
            for action, packets in dev['light'].get('actions', {}).items():
                packets_clean = [clean_hex(p) for p in packets if str(p).strip()]
                if packets_clean:
                    packets_str = ",\n        ".join([f'"{p}"' for p in packets_clean])
                    cpp_code += f"    add_action(devices, \"{light_id}\", \"{action}\", {{\n        {packets_str}\n    }});\n"
        if 'fan' in dev:
            fan_id = dev['fan']['id']
            cpp_code += f"\n    add_device(devices, \"{fan_id}\", \"fan\", \"{dev_name} Fan\");\n"
            for action, packets in dev['fan'].get('actions', {}).items():
                packets_clean = [clean_hex(p) for p in packets if str(p).strip()]
                if packets_clean:
                    packets_str = ",\n        ".join([f'"{p}"' for p in packets_clean])
                    cpp_code += f"    add_action(devices, \"{fan_id}\", \"{action}\", {{\n        {packets_str}\n    }});\n"

    cpp_code += """
}
void DeviceTable::add_device(std::vector<BLEDevice> &devices, std::string id, std::string type, std::string name) {
    BLEDevice device; device.id = id; device.type = type; device.name = name; devices.push_back(device);
}
void DeviceTable::add_action(std::vector<BLEDevice> &devices, std::string device_id, std::string action, std::vector<std::string> packets) {
    for (auto &device : devices) {
        if (device.id == device_id) {
            BLEAction act; act.name = action; act.packets = packets; device.actions[action] = act; return;
        }
    }
}
} // namespace ble_gateway
} // namespace esphome
"""
    cpp_path = os.path.join(base_dir, "components", "ble_gateway", "device_table.cpp")
    with open(cpp_path, 'w', encoding='utf-8') as f:
        f.write(cpp_code)

    # ==========================================
    # 2. 准备动态生成的实体列表 (彻底解决 Duplicate key 问题)
    # ==========================================
    binary_sensors = []
    sensors = []
    text_sensors = []
    buttons = []
    lights_yaml = []
    fans_yaml = []
    tracker_routes = []

    # 【核心修复】：直接将系统级监控传感器注入到列表中，不再使用独立的顶级 key 字符串块
    sensors.append("""  - platform: uptime
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
      - lambda: return min(max(2 * (x + 100.0), 0.0), 100.0);
    unit_of_measurement: "%"
    icon: mdi:wifi-strength-4""")

    text_sensors.append("""  - platform: wifi_info
    ip_address:
      name: "ESP IP Address"
    ssid:
      name: "ESP Connected SSID"
    bssid:
      name: "ESP Connected BSSID\"""")

    buttons.append("""  - platform: restart
    name: "Restart Gateway"
    icon: mdi:restart""")

    # 遍历设备，注入设备级实体
    for dev in devices:
        safe_id = dev['id'].replace('.', '_')
        en_name = get_english_name(dev['id'])
        
        if 'mac' in dev and dev['mac']:
            binary_sensors.append(f"  - platform: template\n    id: {safe_id}_led_state\n    name: \"{en_name} LED\"\n    device_class: light")
            binary_sensors.append(f"  - platform: template\n    id: {safe_id}_fan_state\n    name: \"{en_name} Fan State\"\n    device_class: running")
            sensors.append(f"  - platform: template\n    id: {safe_id}_brightness\n    name: \"{en_name} Brightness\"\n    unit_of_measurement: \"%\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_color_temp\n    name: \"{en_name} Color Temp\"\n    unit_of_measurement: \"K\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_fan_speed\n    name: \"{en_name} Fan Speed\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_timer\n    name: \"{en_name} Timer\"\n    unit_of_measurement: \"min\"\n    accuracy_decimals: 0")
            text_sensors.append(f"  - platform: template\n    id: {safe_id}_fan_direction\n    name: \"{en_name} Fan Direction\"")
            
            route_code = f"""
                if (mac == "{dev['mac'].lower()}") {{
                    id({safe_id}_led_state).publish_state(led_on);
                    id({safe_id}_brightness).publish_state(brightness_pct);
                    id({safe_id}_color_temp).publish_state(color_kelvin);
                    id({safe_id}_fan_state).publish_state(fan_on);
                    id({safe_id}_fan_speed).publish_state(fan_speed);
                    id({safe_id}_fan_direction).publish_state(fan_dir_str);
                    id({safe_id}_timer).publish_state(timer_min);
                }}"""
            tracker_routes.append(route_code)

        if 'light' in dev:
            light_id = dev['light']['id']
            lights_yaml.append(f"  - platform: ble_light\n    id: {safe_id}_light_ctrl\n    name: \"{en_name} Light\"\n    ble_device_id: \"{light_id}\"\n    gateway: ct1_ble")
        if 'fan' in dev:
            fan_id = dev['fan']['id']
            fans_yaml.append(f"  - platform: ble_fan\n    id: {safe_id}_fan_ctrl\n    name: \"{en_name} Fan\"\n    ble_device_id: \"{fan_id}\"\n    gateway: ct1_ble")

    dynamic_tracker = ""
    if tracker_routes:
        dynamic_tracker = """esp32_ble_tracker:
  scan_parameters:
    interval: 320ms
    window: 30ms
    active: false
  on_ble_advertise:
    - then:
        - lambda: |-
            auto datas = x.get_manufacturer_datas();
            for (auto &data : datas) {
                std::string he = "";
                for (uint8_t b : data.data) {
                    char buf[3];
                    sprintf(buf, "%02x", b);
                    he += buf;
                }
                if (he.length() < 40) continue; 
                if (he.substr(0, 4) != "8153") continue;

                std::string mac_raw = he.substr(6, 12);
                std::string mac = "";
                for (int i = 10; i >= 0; i -= 2) {
                    mac += mac_raw.substr(i, 2);
                    if (i > 0) mac += ":";
                }

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
""" + "\n".join(tracker_routes) + "\n                break; \n            }\n"

    # ==========================================
    # 3. 生成 CT1, CT2, CT3 (基础版)
    # ==========================================
    # 【核心修复】：ota 绝对不带 password，确保 web_server v2 前端 100% 显示 OTA 升级按钮！
    base_common = """esphome:
  name: {name}
  friendly_name: {friendly_name}
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
    ssid: "CT Fallback"
    password: "12345678"
api:
  reboot_timeout: 0s
web_server:
  port: 80
  version: 2
ota:
  - platform: esphome
external_components:
  - source:
      type: local
      path: components
ble_gateway:
  id: ct1_ble
"""
    
    def write_yaml(filename, header, extra=""):
        content = header
        if binary_sensors: content += "binary_sensor:\n" + "\n".join(binary_sensors) + "\n\n"
        if sensors: content += "sensor:\n" + "\n".join(sensors) + "\n\n"
        if text_sensors: content += "text_sensor:\n" + "\n".join(text_sensors) + "\n\n"
        if buttons: content += "button:\n" + "\n".join(buttons) + "\n\n"
        if lights_yaml: content += "light:\n" + "\n".join(lights_yaml) + "\n\n"
        if fans_yaml: content += "fan:\n" + "\n".join(fans_yaml) + "\n\n"
        content += extra
        content += dynamic_tracker
        with open(os.path.join(base_dir, filename), 'w', encoding='utf-8') as f:
            f.write(content)

    write_yaml("ct1.yaml", base_common.format(name="ct1", friendly_name="CT1 BLE Gateway (Lite)"))
    write_yaml("ct2.yaml", base_common.format(name="ct2", friendly_name="CT2 BLE Gateway (Full)") + "\nmqtt:\n  broker: \"192.168.6.88\"\n  discovery: true\nbluetooth_proxy:\n  active: false\n")
    write_yaml("ct3.yaml", base_common.format(name="ct3", friendly_name="CT3 BLE Gateway (Custom)"))

    # ==========================================
    # 4. 生成 CT4 (Pro 专属版)
    # ==========================================
    # 【核心修复】：删除了 ct4_base 中硬编码的 sensor 和 text_sensor，统一由列表生成，防止 CT4 也报 Duplicate key
    ct4_base = """esphome:
  name: ct4
  friendly_name: CT4 BLE Gateway (Pro)
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
    ssid: "CT Fallback"
    password: "12345678"
captive_portal:
web_server:
  port: 80
  version: 2
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
light:
  - platform: binary
    name: Blue LED
    id: blue_led
    output: blue_led_out
    restore_mode: RESTORE_DEFAULT_OFF
  - platform: binary
    name: White LED
    id: white_led
    output: white_led_out
    restore_mode: RESTORE_DEFAULT_OFF
ble_gateway:
  id: ct1_ble
"""

    keys_yaml = """
  - platform: gpio
    id: key1
    name: KEY1
    pin: { number: GPIO34, inverted: true }
    filters: [delayed_on: 20ms, delayed_off: 20ms]
    on_multi_click:
      - timing: [ON for at least 8s]
        then:
          - if: { condition: { binary_sensor.is_on: key4 }, then: [delay: 500ms, if: { condition: { binary_sensor.is_on: key4 }, then: [lambda: 'id(do_factory_reset) = true;', repeat: { count: 5, then: [light.toggle: white_led, delay: 100ms] }, lambda: 'App.reboot();' ] }] }
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
      - timing: [ON for at most 0.5s, OFF for at most 0.3s, ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key2", mode: "double" } }]
      - timing: [ON for at most 0.5s, OFF for at least 0.3s]
        then:
          - light.turn_on: blue_led
          - delay: 200ms
          - light.turn_off: blue_led
          - homeassistant.event: { event: esphome.gateway_key, data: { key: "key2", mode: "single" } }
          - lambda: 'id(safe_mode_tap_count)++;'
          - if:
              condition: { lambda: 'return id(safe_mode_tap_count) >= 5;' }
              then: [lambda: 'id(safe_mode_tap_count) = 0;', repeat: { count: 8, then: [light.toggle: blue_led, delay: 150ms] }, lambda: 'App.safe_reboot();']
              else: [delay: 5000ms, lambda: 'id(safe_mode_tap_count) = 0;']

  - platform: gpio
    id: key3
    name: KEY3
    pin: { number: GPIO32, inverted: true }
    filters: [delayed_on: 20ms, delayed_off: 20ms]
    on_multi_click:
      - timing: [ON for at least 1.5s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key3", mode: "long" } }]
      - timing: [ON for at most 0.5s, OFF for at most 0.3s, ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key3", mode: "double" } }]
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
      - timing: [ON for at most 0.5s, OFF for at most 0.3s, ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key4", mode: "double" } }]
      - timing: [ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key4", mode: "single" } }]
"""

    # 组装 CT4 YAML
    ct4_content = ct4_base
    if binary_sensors: 
        ct4_content += "binary_sensor:\n" + "\n".join(binary_sensors) + keys_yaml + "\n\n"
    else:
        ct4_content += "binary_sensor:\n" + keys_yaml + "\n\n"
        
    if sensors: ct4_content += "sensor:\n" + "\n".join(sensors) + "\n\n"
    if text_sensors: ct4_content += "text_sensor:\n" + "\n".join(text_sensors) + "\n\n"
    if buttons: ct4_content += "button:\n" + "\n".join(buttons) + "\n\n"
    if lights_yaml: ct4_content += "light:\n" + "\n".join(lights_yaml) + "\n\n"
    if fans_yaml: ct4_content += "fan:\n" + "\n".join(fans_yaml) + "\n\n"
    ct4_content += dynamic_tracker

    with open(os.path.join(base_dir, "ct4.yaml"), 'w', encoding='utf-8') as f:
        f.write(ct4_content)

    print(f"🎉 Successfully generated: {cpp_path}")
    print(f"🎉 Successfully generated: ct1/2/3/4.yaml (Fixed Duplicate Key & HTTP OTA)")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, "devices_config")
    if not os.path.exists(config_dir):
        print(f"❌ Error: Directory {config_dir} not found.")
        exit(1)
    generate_all(config_dir, base_dir)
