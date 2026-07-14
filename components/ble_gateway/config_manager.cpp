#include "config_manager.h"
#include "device_table.h"

namespace esphome {
namespace ble_gateway {

void ConfigManager::load() {
    devices_.clear();
    index_.clear();

    DeviceTable table;
    table.load(devices_);

    // 预分配内存，避免 unordered_map 在插入过程中多次 rehash
    index_.reserve(devices_.size());
    for (size_t i = 0; i < devices_.size(); i++) {
        index_.emplace(devices_[i].id, i);
    }
}

const BLEDevice *ConfigManager::find_device(const std::string &device_id) const {
    auto it = index_.find(device_id);
    return (it == index_.end()) ? nullptr : &devices_[it->second];
}

const BLEAction *ConfigManager::find_action(const std::string &device_id,
                                            const std::string &action) const {
    const BLEDevice *dev = find_device(device_id);
    if (!dev) return nullptr;
    
    auto it = dev->actions.find(action);
    return (it == dev->actions.end()) ? nullptr : &it->second;
}

bool ConfigManager::get_action(const std::string &device_id,
                               const std::string &action,
                               BLEAction &result) const {
    const BLEAction *p = find_action(device_id, action);
    if (!p) return false;
    result = *p; // 此处发生深拷贝，仅用于向后兼容
    return true;
}

}  // namespace ble_gateway
}  // namespace esphome
