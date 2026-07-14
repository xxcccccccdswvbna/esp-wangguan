#pragma once

#include <string>

namespace esphome {
namespace ble_gateway {

// 前向声明：打破循环依赖，保持头文件轻量，加速编译
class BLEGateway;
class ConfigManager;

class CommandRouter {
public:
    void set_gateway(BLEGateway *gateway) { gateway_ = gateway; }
    void set_config(ConfigManager *config) { config_ = config; }

    // 发送命令的核心接口
    bool send_command(const std::string &device, const std::string &action);

private:
    BLEGateway    *gateway_{nullptr};
    ConfigManager *config_{nullptr};
};

}  // namespace ble_gateway
}  // namespace esphome
