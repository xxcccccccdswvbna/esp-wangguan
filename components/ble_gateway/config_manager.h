#pragma once

#include "device_model.h"
#include <string>
#include <unordered_map>
#include <vector>

namespace esphome {
namespace ble_gateway {

class ConfigManager {
public:
    // 从 DeviceTable 加载数据并构建索引
    void load();

    // O(1) 查询设备；未命中返回 nullptr。命中返回 const 指针，零拷贝。
    const BLEDevice *find_device(const std::string &device_id) const;
    
    // O(1) 查询动作；未命中返回 nullptr。命中返回 const 指针，零拷贝。
    const BLEAction *find_action(const std::string &device_id,
                                 const std::string &action) const;

    // 兼容旧版接口的深拷贝方法（新代码建议优先使用 find_action）
    bool get_action(const std::string &device_id,
                    const std::string &action,
                    BLEAction &result) const;

    // 获取所有设备的只读引用
    const std::vector<BLEDevice> &devices() const { return devices_; }

private:
    std::vector<BLEDevice> devices_;
    // 核心优化：使用 unordered_map 建立 device_id 到 vector 索引的映射，实现 O(1) 查找
    std::unordered_map<std::string, size_t> index_;   
};

}  // namespace ble_gateway
}  // namespace esphome
