import json
import os
import glob

def clean_hex(hex_str):
    """清理 HEX 字符串：去除 0x 前缀，去除空格，统一大写"""
    hex_str = str(hex_str).strip().replace(" ", "").replace("0x", "").replace("0X", "")
    return hex_str.upper()

def generate_cpp(config_dir, cpp_path):
    print(f"📂 正在扫描配置目录: {config_dir}")
    
    # 获取目录下所有的 .json 文件
    json_files = glob.glob(os.path.join(config_dir, "*.json"))
    
    if not json_files:
        print("⚠️ 警告: 未找到任何 .json 配置文件！")
        return

    all_devices = []
    
    # 1. 遍历并合并所有 JSON 文件
    for json_file in sorted(json_files): # sorted 保证每次生成顺序一致，避免 Git 频繁变动
        print(f"  ✅ 读取: {os.path.basename(json_file)}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                device_data = json.load(f)
                all_devices.append(device_data)
        except json.JSONDecodeError as e:
            print(f"  ❌ 错误: {os.path.basename(json_file)} 格式无效! {e}")
            return

    print(f"🚀 正在生成 C++ 代码 (共 {len(all_devices)} 个设备)...")
    
    cpp_code = """#include "device_table.h"

namespace esphome {
namespace ble_gateway {

void DeviceTable::load(std::vector<BLEDevice> &devices) {
"""
    
    # 2. 生成 C++ 代码
    for dev in all_devices:
        dev_id = dev.get('id', 'unknown')
        dev_type = dev.get('type', 'unknown')
        dev_name = dev.get('name', 'Unknown Device')
        
        cpp_code += f"""
    /* ==========================================
     * 设备: {dev_name} ({dev_id})
     * ========================================== */
    add_device(devices, "{dev_id}", "{dev_type}", "{dev_name}");
"""
        for action_name, packets in dev.get('actions', {}).items():
            # 清理并格式化 HEX 数据
            packets_clean = [clean_hex(p) for p in packets if str(p).strip()]
            if not packets_clean:
                continue
                
            packets_str = ",\n        ".join([f'"{p}"' for p in packets_clean])
            
            cpp_code += f"""
    /* 动作: {action_name} */
    add_action(devices, "{dev_id}", "{action_name}", {{
        {packets_str}
    }});
"""

    # 3. 拼接底部的 C++ 辅助函数实现
    cpp_code += """
}

void DeviceTable::add_device(
    std::vector<BLEDevice> &devices,
    std::string id,
    std::string type,
    std::string name
) {
    BLEDevice device;
    device.id = id;
    device.type = type;
    device.name = name;
    devices.push_back(device);
}

void DeviceTable::add_action(
    std::vector<BLEDevice> &devices,
    std::string device_id,
    std::string action,
    std::vector<std::string> packets
) {
    for (auto &device : devices) {
        if (device.id == device_id) {
            BLEAction act;
            act.name = action;
            act.packets = packets;
            device.actions[action] = act;
            return;
        }
    }
}

} // namespace ble_gateway
} // namespace esphome
"""

    # 4. 写入 C++ 文件
    with open(cpp_path, 'w', encoding='utf-8') as f:
        f.write(cpp_code)
    print(f"🎉 成功生成 C++ 代码: {cpp_path}")

if __name__ == "__main__":
    # 获取脚本所在目录（即项目根目录）
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 配置目录路径
    config_dir = os.path.join(base_dir, "devices_config")
    cpp_file = os.path.join(base_dir, "components", "ble_gateway", "device_table.cpp")
    
    if not os.path.exists(config_dir):
        print(f"❌ 错误: 找不到配置目录 {config_dir}，请先创建该文件夹并放入 .json 文件。")
        exit(1)
    else:
        generate_cpp(config_dir, cpp_file)
