#pragma once

#include <map>
#include <string>
#include <vector>

namespace esphome {
namespace ble_gateway {

struct BLEAction {
    std::string name;
    std::vector<std::string> packets;
};

struct BLEDevice {
    std::string id;
    std::string type;
    std::string name;
    std::string mac;       // 🔥 新增
    std::string protocol;  // 🔥 新增
    std::map<std::string, BLEAction> actions;   
};

}  // namespace ble_gateway
}  // namespace esphome
