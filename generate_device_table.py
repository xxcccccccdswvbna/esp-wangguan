import json
import os
import glob

def clean_hex(hex_str):
    hex_str = str(hex_str).strip().replace(" ", "").replace("0x", "").replace("0X", "")
    return hex_str.upper()

def generate_all(config_dir, base_dir):
    print(f"📂 正在扫描配置目录: {config_dir}")
    json_files = sorted(glob.glob(os.path.join(config_dir, "*.json")))
    
    if not json_files:
        print("⚠️ 警告: 未找到任何 .json 配置文件！")
        return

    devices = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'id' in data and 'name' in data:
                    devices.append(data)
                    print(f"  ✅ 读取: {data['name']}")
        except json.JSONDecodeError as e:
            print(f"  ❌ 错误: {os.path.basename(json_file)} 格式无效! {e}")
            return

    print(f"🚀 正在智能生成完整代码 (共 {len(devices)} 个设备)...")

    # ==========================================
    # 1. 生成 C++ device_table.cpp
    # ==========================================
    cpp_code = """#include "device_table.h"

namespace esphome {
namespace ble_gateway {

void DeviceTable::load(std::vector<BLEDevice> &devices) {
"""
    for dev in devices:
        dev_name = dev['name']
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
    # 2. 直接生成完整的 ct1.yaml
    # ==========================================
    
    # --- 基础配置 (硬编码) ---
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

    # --- 动态生成实体和传感器 ---
    binary_sensors = []
    sensors = []
    text_sensors = []
    lights = []
    fans = []
    tracker_routes = []

    for dev in devices:
        safe_id = dev['id'].replace('.', '_')
        name_prefix = dev['name']
        
        # 有 MAC 才生成状态和路由
        if 'mac' in dev and dev['mac']:
            binary_sensors.append(f"  - platform: template\n    id: {safe_id}_led_state\n    name: \"{name_prefix} LED\"\n    device_class: light")
            binary_sensors.append(f"  - platform: template\n    id: {safe_id}_fan_state\n    name: \"{name_prefix} 风扇状态\"\n    device_class: running")
            
            sensors.append(f"  - platform: template\n    id: {safe_id}_brightness\n    name: \"{name_prefix} 亮度\"\n    unit_of_measurement: \"%\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_color_temp\n    name: \"{name_prefix} 色温\"\n    unit_of_measurement: \"K\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_fan_speed\n    name: \"{name_prefix} 风扇档位\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_timer\n    name: \"{name_prefix} 定时\"\n    unit_of_measurement: \"min\"\n    accuracy_decimals: 0")
            
            text_sensors.append(f"  - platform: template\n    id: {safe_id}_fan_direction\n    name: \"{name_prefix} 风扇方向\"")
            
            mac_bytes = dev['mac'].split(':')
            mac_array = "{" + ", ".join([f"0x{b}" for b in reversed(mac_bytes)]) + "}"
            route_code = f"""
                uint8_t mac_target_{safe_id}[6] = {mac_array};
                if (memcmp(current_mac, mac_target_{safe_id}, 6) == 0) {{
                    id({safe_id}_led_state).publish_state(led_on);
                    id({safe_id}_brightness).publish_state(brightness_pct);
                    id({safe_id}_color_temp).publish_state(color_kelvin);
                    id({safe_id}_fan_state).publish_state(fan_on);
                    id({safe_id}_fan_speed).publish_state(fan_speed);
                    id({safe_id}_fan_direction).publish_state(fan_dir_str);
                    id({safe_id}_timer).publish_state(timer_min);
                }}"""
            tracker_routes.append(route_code)

        # 有 light/fan 节点才生成控制实体
        if 'light' in dev:
            light_id = dev['light']['id']
            lights.append(f"  - platform: ble_light\n    id: {safe_id}_light_ctrl\n    name: \"{name_prefix} 灯\"\n    ble_device_id: \"{light_id}\"\n    gateway: ct1_ble")
            
        if 'fan' in dev:
            fan_id = dev['fan']['id']
            fans.append(f"  - platform: ble_fan\n    id: {safe_id}_fan_ctrl\n    name: \"{name_prefix} 风扇\"\n    ble_device_id: \"{fan_id}\"\n    gateway: ct1_ble")

    # 拼接 YAML 块
    if binary_sensors: yaml_content += "binary_sensor:\n" + "\n".join(binary_sensors) + "\n\n"
    if sensors: yaml_content += "sensor:\n" + "\n".join(sensors) + "\n\n"
    if text_sensors: yaml_content += "text_sensor:\n" + "\n".join(text_sensors) + "\n\n"
    if lights: yaml_content += "light:\n" + "\n".join(lights) + "\n\n"
    if fans: yaml_content += "fan:\n" + "\n".join(fans) + "\n\n"
    
    # 拼接 Tracker
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
                auto &raw = data.data;
                if (raw.size() < 20) continue; 
                if (raw[0] != 0x81 || raw[1] != 0x53) continue;

                uint8_t mode = raw[11];
                bool led_on = (mode & 0x01) != 0;
                bool fan_on = !(mode == 0x10 || mode == 0x11);
                bool fan_reverse = (mode & 0x20) != 0;
                
                float brightness_pct = (raw[14] / 255.0f) * 100.0f;
                float color_kelvin = 2700.0f + (6500.0f - 2700.0f) * (raw[15] / 255.0f);
                int timer_min = (raw[16] << 8) | raw[17];
                int fan_speed = fan_on ? (raw[18] + 1) : 0;
                std::string fan_dir_str = fan_on ? (fan_reverse ? "Reverse" : "Forward") : "Off";

                uint8_t current_mac[6] = {raw[8], raw[7], raw[6], raw[5], raw[4], raw[3]};
"""
        tracker_yaml += "\n".join(tracker_routes)
        tracker_yaml += "\n            }\n"
        yaml_content += tracker_yaml

    # 写入完整的 ct1.yaml
    yaml_path = os.path.join(base_dir, "ct1.yaml")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    print(f"🎉 成功生成: {cpp_path}")
    print(f"🎉 成功生成: {yaml_path} (完整可编译版)")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, "devices_config")
    if not os.path.exists(config_dir):
        print(f"❌ 错误: 找不到 {config_dir}")
        exit(1)
    generate_all(config_dir, base_dir)
