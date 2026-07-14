#pragma once

#include "device_model.h"
#include <string>
#include <vector>

namespace esphome {
namespace ble_gateway {

// 由 Python 脚本自动生成的静态设备表加载器
class DeviceTable {
public:
    // 加载所有设备数据到传入的容器中
    void load(std::vector<BLEDevice> &devices);

private:
    // 辅助方法：使用 const ref 避免不必要的字符串拷贝
    static void add_device(std::vector<BLEDevice> &devices,
                           const std::string &id,
                           const std::string &type,
                           const std::string &name);

    // 辅助方法：使用 std::move 语义高效转移 packets 数据
    static void add_action(std::vector<BLEDevice> &devices,
                           const std::string &device_id,
                           const std::string &action,
                           std::vector<std::string> packets);
};

}  // namespace ble_gateway
}  // namespace esphome
