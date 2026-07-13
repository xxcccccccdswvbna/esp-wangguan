import json
import os
import glob

def clean_hex(hex_str):
    hex_str = str(hex_str).strip().replace(" ", "").replace("0x", "").replace("0X", "")
    return hex_str.upper()

def get_english_name(dev_id):
    """根据 id (如 device.room1) 生成纯英文基础名 (如 Room1)，防止 HA 中文转码冲突"""
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
    # 准备数据容器
    # ==========================================
    cpp_code = """#include "device_table.h"

namespace esphome {
namespace ble_gateway {

void DeviceTable::load(std::vector<BLEDevice> &devices) {
"""
    binary_sensors = []
    sensors = []
    text_sensors = []
    lights_yaml = []
    fans_yaml = []
    tracker_routes = []

    for dev in devices:
        safe_id = dev['id'].replace('.', '_')
        en_name = get_english_name(dev['id'])
        
        # ==========================================
        # 【规则 A】：有 MAC -> 只负责生成 状态传感器 和 监听路由
        # ==========================================
        if 'mac' in dev and dev['mac']:
            # 1. 生成状态传感器
            binary_sensors.append(f"  - platform: template\n    id: {safe_id}_led_state\n    name: \"{en_name} LED\"\n    device_class: light")
            binary_sensors.append(f"  - platform: template\n    id: {safe_id}_fan_state\n    name: \"{en_name} Fan State\"\n    device_class: running")
            
            sensors.append(f"  - platform: template\n    id: {safe_id}_brightness\n    name: \"{en_name} Brightness\"\n    unit_of_measurement: \"%\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_color_temp\n    name: \"{en_name} Color Temp\"\n    unit_of_measurement: \"K\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_fan_speed\n    name: \"{en_name} Fan Speed\"\n    accuracy_decimals: 0")
            sensors.append(f"  - platform: template\n    id: {safe_id}_timer\n    name: \"{en_name} Timer\"\n    unit_of_measurement: \"min\"\n    accuracy_decimals: 0")
            
            text_sensors.append(f"  - platform: template\n    id: {safe_id}_fan_direction\n    name: \"{en_name} Fan Direction\"")
            
            # 2. 生成 BLE 监听路由 (Tracker)
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

        # ==========================================
        # 【规则 B】：有 light 节点(发射数据) -> 只负责生成 灯控制实体 和 C++指令
        # ==========================================
        if 'light' in dev:
            light_id = dev['light']['id']
            # 生成 YAML 控制实体
            lights_yaml.append(f"  - platform: ble_light\n    id: {safe_id}_light_ctrl\n    name: \"{en_name} Light\"\n    ble_device_id: \"{light_id}\"\n    gateway: ct1_ble")
            # 生成 C++ 底层指令
            cpp_code += f"\n    add_device(devices, \"{light_id}\", \"light\", \"{en_name} Light\");\n"
            for action, packets in dev['light'].get('actions', {}).items():
                packets_clean = [clean_hex(p) for p in packets if str(p).strip()]
                if packets_clean:
                    packets_str = ",\n        ".join([f'"{p}"' for p in packets_clean])
                    cpp_code += f"    add_action(devices, \"{light_id}\", \"{action}\", {{\n        {packets_str}\n    }});\n"

        # ==========================================
        # 【规则 C】：有 fan 节点(发射数据) -> 只负责生成 风扇控制实体 和 C++指令
        # ==========================================
        if 'fan' in dev:
            fan_id = dev['fan']['id']
            # 生成 YAML 控制实体
            fans_yaml.append(f"  - platform: ble_fan\n    id: {safe_id}_fan_ctrl\n    name: \"{en_name} Fan\"\n    ble_device_id: \"{fan_id}\"\n    gateway: ct1_ble")
            # 生成 C++ 底层指令
            cpp_code += f"\n    add_device(devices, \"{fan_id}\", \"fan\", \"{en_name} Fan\");\n"
            for action, packets in dev['fan'].get('actions', {}).items():
                packets_clean = [clean_hex(p) for p in packets if str(p).strip()]
                if packets_clean:
                    packets_str = ",\n        ".join([f'"{p}"' for p in packets_clean])
                    cpp_code += f"    add_action(devices, \"{fan_id}\", \"{action}\", {{\n        {packets_str}\n    }});\n"

    # 闭合 C++ 代码
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

    # ==========================================
    # 组装完整的 ct1.yaml
    # ==========================================
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
    # 按规则拼接 YAML 块
    if binary_sensors: yaml_content += "binary_sensor:\n" + "\n".join(binary_sensors) + "\n\n"
    if sensors: yaml_content += "sensor:\n" + "\n".join(sensors) + "\n\n"
    if text_sensors: yaml_content += "text_sensor:\n" + "\n".join(text_sensors) + "\n\n"
    if lights_yaml: yaml_content += "light:\n" + "\n".join(lights_yaml) + "\n\n"
    if fans_yaml: yaml_content += "fan:\n" + "\n".join(fans_yaml) + "\n\n"
    
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

    # ==========================================
    # 写入文件
    # ==========================================
    cpp_path = os.path.join(base_dir, "components", "ble_gateway", "device_table.cpp")
    with open(cpp_path, 'w', encoding='utf-8') as f:
        f.write(cpp_code)

    yaml_path = os.path.join(base_dir, "ct1.yaml")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    print(f"🎉 Successfully generated: {cpp_path}")
    print(f"🎉 Successfully generated: {yaml_path} (Strictly decoupled logic)")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, "devices_config")
    if not os.path.exists(config_dir):
        print(f"❌ Error: Directory {config_dir} not found.")
        exit(1)
    generate_all(config_dir, base_dir)
