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
    # 1. 生成 C++ device_table.cpp
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
    # 2. 生成完整的 ct1.yaml (包含三大件 + 你验证过的 OK 解析逻辑)
    # ==========================================
    
    # --- 基础配置 (加入 HTTP, MQTT, BT Proxy) ---
    yaml_content = """esphome:
  name: ct1
  friendly_name: CT1 BLE Gateway

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

# 1. 开启 HTTP 网页服务 (用于本地 OTA 升级)
web_server:
  port: 80
  version: 2

# 2. 开启 MQTT
mqtt:
  broker: "192.168.6.88"
  discovery: true
  on_message:
    - topic: "ct1/ble/send"
      then:
        - lambda: |-
            id(ct1_ble).send_hex(x);

# 3. 开启蓝牙代理 (被动模式，节省资源)
bluetooth_proxy:
  active: false

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

    # --- 动态生成实体 ---
    binary_sensors = []
    sensors = []
    text_sensors = []
    lights_yaml = []
    fans_yaml = []
    tracker_routes = []

    for dev in devices:
        safe_id = dev['id'].replace('.', '_')
        en_name = get_english_name(dev['id'])
        
        # 规则 A: 有 MAC -> 生成状态传感器
        if 'mac' in dev and dev['mac']:
            binary_sensors.append(f"  - platform: template\n    id: {safe_id}_led_state\n    name: \"{en_name} LED\"\n    device_class: light")
            binary_sensors.append(f"  - platform: template\n    id: {safe_id}_fan_state\n    name: \"{en_name} Fan State\"\n    device_class: running")
            
            sensors.append(f"  - platform: template\n    id: {safe_id}_brightness\n    name: \"{en_name} Brightness\"\n    unit_of_measurement: \"%\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_color_temp\n    name: \"{en_name} Color Temp\"\n    unit_of_measurement: \"K\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_fan_speed\n    name: \"{en_name} Fan Speed\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_timer\n    name: \"{en_name} Timer\"\n    unit_of_measurement: \"min\"\n    accuracy_decimals: 0")
            
            text_sensors.append(f"  - platform: template\n    id: {safe_id}_fan_direction\n    name: \"{en_name} Fan Direction\"")
            
            # 动态生成路由判断 (完全保留你的字符串解析逻辑)
            route_code = f"""
                // 【Device: {en_name}】
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

        # 规则 B & C: 有 light/fan -> 生成控制实体
        if 'light' in dev:
            light_id = dev['light']['id']
            lights_yaml.append(f"  - platform: ble_light\n    id: {safe_id}_light_ctrl\n    name: \"{en_name} Light\"\n    ble_device_id: \"{light_id}\"\n    gateway: ct1_ble")
            
        if 'fan' in dev:
            fan_id = dev['fan']['id']
            fans_yaml.append(f"  - platform: ble_fan\n    id: {safe_id}_fan_ctrl\n    name: \"{en_name} Fan\"\n    ble_device_id: \"{fan_id}\"\n    gateway: ct1_ble")

    # 拼接 YAML
    if binary_sensors: yaml_content += "binary_sensor:\n" + "\n".join(binary_sensors) + "\n\n"
    if sensors: yaml_content += "sensor:\n" + "\n".join(sensors) + "\n\n"
    if text_sensors: yaml_content += "text_sensor:\n" + "\n".join(text_sensors) + "\n\n"
    if lights_yaml: yaml_content += "light:\n" + "\n".join(lights_yaml) + "\n\n"
    if fans_yaml: yaml_content += "fan:\n" + "\n".join(fans_yaml) + "\n\n"
    
    # --- 核心：完全保留你验证过的 OK 的 BLE 字符串解析逻辑 ---
    if tracker_routes:
        tracker_yaml = """esp32_ble_tracker:
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

                // 提取并反转 MAC 地址 (位置 6:18)
                std::string mac_raw = he.substr(6, 12);
                std::string mac = "";
                for (int i = 10; i >= 0; i -= 2) {
                    mac += mac_raw.substr(i, 2);
                    if (i > 0) mac += ":";
                }

                // 解析通用状态数据
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

                // === 根据 MAC 地址路由到对应的设备 ===
"""
        tracker_yaml += "\n".join(tracker_routes)
        tracker_yaml += "\n                \n                break; \n            }"
        yaml_content += tracker_yaml

    # 写入 ct1.yaml
    yaml_path = os.path.join(base_dir, "ct1.yaml")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    print(f"🎉 Successfully generated: {cpp_path}")
    print(f"🎉 Successfully generated: {yaml_path} (With Web, MQTT, BT Proxy & Verified Logic)")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, "devices_config")
    if not os.path.exists(config_dir):
        print(f"❌ Error: Directory {config_dir} not found.")
        exit(1)
    generate_all(config_dir, base_dir)
