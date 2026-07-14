#pragma once

#include <map>
#include <string>
#include <vector>

namespace esphome {
namespace ble_gateway {

// 单个动作的数据结构
struct BLEAction {
    std::string name;
    std::vector<std::string> packets;
};

// 单个 BLE 设备的数据结构
struct BLEDevice {
    std::string id;
    std::string type;
    std::string name;
    // 每个设备的动作数量通常很少，使用 std::map 便于按键名快速查找和调试
    std::map<std::string, BLEAction> actions;   
};

}  // namespace ble_gateway
}  // namespace esphome
