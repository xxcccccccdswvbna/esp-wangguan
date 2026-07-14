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
    # 2. 准备动态生成的实体和 Tracker 部分 (所有版本共用)
    # ==========================================
    binary_sensors = []
    sensors = []
    text_sensors = []
    lights_yaml = []
    fans_yaml = []
    tracker_routes = []

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

        if 'light' in dev:
            light_id = dev['light']['id']
            lights_yaml.append(f"  - platform: ble_light\n    id: {safe_id}_light_ctrl\n    name: \"{en_name} Light\"\n    ble_device_id: \"{light_id}\"\n    gateway: ct1_ble")
        if 'fan' in dev:
            fan_id = dev['fan']['id']
            fans_yaml.append(f"  - platform: ble_fan\n    id: {safe_id}_fan_ctrl\n    name: \"{en_name} Fan\"\n    ble_device_id: \"{fan_id}\"\n    gateway: ct1_ble")

    dynamic_yaml = ""
    if binary_sensors: dynamic_yaml += "binary_sensor:\n" + "\n".join(binary_sensors) + "\n\n"
    if sensors: dynamic_yaml += "sensor:\n" + "\n".join(sensors) + "\n\n"
    if text_sensors: dynamic_yaml += "text_sensor:\n" + "\n".join(text_sensors) + "\n\n"
    if lights_yaml: dynamic_yaml += "light:\n" + "\n".join(lights_yaml) + "\n\n"
    if fans_yaml: dynamic_yaml += "fan:\n" + "\n".join(fans_yaml) + "\n\n"
    
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
"""
        tracker_yaml += "\n".join(tracker_routes)
        tracker_yaml += "\n                break; \n            }\n"
        dynamic_yaml += tracker_yaml

    # ==========================================
    # 3. 生成 3 个不同版本的 YAML 文件 (强制全部包含 HTTP OTA)
    # ==========================================
    
    # 【核心修改】：将 web_server 和 ota 提取到 base_common，确保所有版本 100% 具备 HTTP 升级能力！
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

# ==========================================
# 【强制核心配置】：确保所有版本都具备 HTTP 网页升级能力
# ==========================================
web_server:
  port: 80
  version: 2

ota:
  - platform: esphome
    # password: "your_ota_password" # 如需密码请取消注释，网页升级时需输入

external_components:
  - source:
      type: local
      path: components

ble_gateway:
  id: ct1_ble

"""

    # --- CT1: 精简保命版 (纯净，最稳定) ---
    ct1_header = base_common.format(name="ct1", friendly_name="CT1 BLE Gateway (Lite)")
    # ct1 不需要额外添加东西，直接使用 base_common
    with open(os.path.join(base_dir, "ct1.yaml"), 'w', encoding='utf-8') as f:
        f.write(ct1_header + dynamic_yaml)

    # --- CT2: 全功能版 (包含 MQTT + 蓝牙代理) ---
    ct2_header = base_common.format(name="ct2", friendly_name="CT2 BLE Gateway (Full)")
    ct2_header += """
# CT2 专属扩展功能
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
    with open(os.path.join(base_dir, "ct2.yaml"), 'w', encoding='utf-8') as f:
        f.write(ct2_header + dynamic_yaml)

    # --- CT3: 定制扩展版 (预留接口，同样带 HTTP 升级) ---
    ct3_header = base_common.format(name="ct3", friendly_name="CT3 BLE Gateway (Custom)")
    ct3_header += """
# CT3 专属扩展功能 (示例：此处可添加你需要的特定组件，如 deep_sleep 等)
# 注意：本版本同样保留了 web_server，确保可以通过 HTTP 升级！
"""
    with open(os.path.join(base_dir, "ct3.yaml"), 'w', encoding='utf-8') as f:
        f.write(ct3_header + dynamic_yaml)

    print(f"🎉 Successfully generated: {cpp_path}")
    print(f"🎉 Successfully generated: ct1.yaml (Lite + HTTP OTA)")
    print(f"🎉 Successfully generated: ct2.yaml (Full + HTTP OTA)")
    print(f"🎉 Successfully generated: ct3.yaml (Custom + HTTP OTA)")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, "devices_config")
    if not os.path.exists(config_dir):
        print(f"❌ Error: Directory {config_dir} not found.")
        exit(1)
    generate_all(config_dir, base_dir)
