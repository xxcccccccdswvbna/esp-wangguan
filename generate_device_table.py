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
                if 'id' in data and 'mac' in data and 'name' in data:
                    devices.append(data)
                    print(f"  ✅ 读取物理设备: {data['name']} ({data['mac']})")
                else:
                    print(f"  ⚠️ 跳过: {os.path.basename(json_file)} (缺少 id, mac 或 name)")
        except json.JSONDecodeError as e:
            print(f"  ❌ 错误: {os.path.basename(json_file)} 格式无效! {e}")
            return

    print(f"🚀 正在生成代码 (共 {len(devices)} 个物理设备)...")

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
        
        # 处理灯
        if 'light' in dev:
            light_id = dev['light']['id']
            cpp_code += f"\n    add_device(devices, \"{light_id}\", \"light\", \"{dev_name} Light\");\n"
            for action, packets in dev['light'].get('actions', {}).items():
                packets_clean = [clean_hex(p) for p in packets if str(p).strip()]
                if packets_clean:
                    packets_str = ",\n        ".join([f'"{p}"' for p in packets_clean])
                    cpp_code += f"    add_action(devices, \"{light_id}\", \"{action}\", {{\n        {packets_str}\n    }});\n"
                    
        # 处理风扇
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
    with open(os.path.join(base_dir, "components", "ble_gateway", "device_table.cpp"), 'w', encoding='utf-8') as f:
        f.write(cpp_code)

    # ==========================================
    # 2. 生成 auto_entities.yaml
    # ==========================================
    yaml_entities = "binary_sensor:\nsensor:\ntext_sensor:\nlight:\nfan:\n"

    for dev in devices:
        safe_id = dev['id'].replace('.', '_')
        name_prefix = dev['name']
        
        # 生成状态传感器 (因为灯和风扇状态在同一个广播包里，所以一起生成)
        yaml_entities += f"""
  - platform: template
    id: {safe_id}_led_state
    name: "{name_prefix} LED"
    device_class: light
  - platform: template
    id: {safe_id}_fan_state
    name: "{name_prefix} 风扇状态"
    device_class: running
  - platform: template
    id: {safe_id}_brightness
    name: "{name_prefix} 亮度"
    unit_of_measurement: "%"
    accuracy_decimals: 0
  - platform: template
    id: {safe_id}_color_temp
    name: "{name_prefix} 色温"
    unit_of_measurement: "K"
    accuracy_decimals: 0
  - platform: template
    id: {safe_id}_fan_speed
    name: "{name_prefix} 风扇档位"
    accuracy_decimals: 0
  - platform: template
    id: {safe_id}_timer
    name: "{name_prefix} 定时"
    unit_of_measurement: "min"
    accuracy_decimals: 0
  - platform: template
    id: {safe_id}_fan_direction
    name: "{name_prefix} 风扇方向"
"""
        # 生成控制实体 (根据 JSON 中是否有 light/fan 节点决定)
        if 'light' in dev:
            light_id = dev['light']['id']
            yaml_entities += f"""
  - platform: ble_light
    id: {safe_id}_light_ctrl
    name: "{name_prefix} 灯"
    ble_device_id: "{light_id}"
    gateway: ct1_ble
"""
        if 'fan' in dev:
            fan_id = dev['fan']['id']
            yaml_entities += f"""
  - platform: ble_fan
    id: {safe_id}_fan_ctrl
    name: "{name_prefix} 风扇"
    ble_device_id: "{fan_id}"
    gateway: ct1_ble
"""

    with open(os.path.join(base_dir, "auto_entities.yaml"), 'w', encoding='utf-8') as f:
        f.write(yaml_entities)

    # ==========================================
    # 3. 生成 auto_tracker.yaml (BLE 监听路由)
    # ==========================================
    tracker_code = """esp32_ble_tracker:
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

                // 解析通用状态 (灯和风扇共用同一个广播包)
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
    for dev in devices:
        safe_id = dev['id'].replace('.', '_')
        mac_bytes = dev['mac'].split(':')
        mac_array = "{" + ", ".join([f"0x{b}" for b in reversed(mac_bytes)]) + "}"
        
        tracker_code += f"""
                // 路由: {dev['name']} ({dev['mac']})
                uint8_t mac_target_{safe_id}[6] = {mac_array};
                if (memcmp(current_mac, mac_target_{safe_id}, 6) == 0) {{
                    id({safe_id}_led_state).publish_state(led_on);
                    id({safe_id}_brightness).publish_state(brightness_pct);
                    id({safe_id}_color_temp).publish_state(color_kelvin);
                    id({safe_id}_fan_state).publish_state(fan_on);
                    id({safe_id}_fan_speed).publish_state(fan_speed);
                    id({safe_id}_fan_direction).publish_state(fan_dir_str);
                    id({safe_id}_timer).publish_state(timer_min);
                }}
"""
    tracker_code += "            }\n"

    with open(os.path.join(base_dir, "auto_tracker.yaml"), 'w', encoding='utf-8') as f:
        f.write(tracker_code)

    print("🎉 成功生成: device_table.cpp, auto_entities.yaml, auto_tracker.yaml")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, "devices_config")
    if not os.path.exists(config_dir):
        print(f"❌ 错误: 找不到 {config_dir}")
        exit(1)
    generate_all(config_dir, base_dir)
