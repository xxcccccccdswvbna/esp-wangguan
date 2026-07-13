#include "command_router.h"
#include "ble_gateway.h"
#include "config_manager.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_gateway {

static const char *TAG = "command_router";

void CommandRouter::set_gateway(BLEGateway *gateway) {
    gateway_ = gateway;
}

void CommandRouter::set_config(ConfigManager *config) {
    config_ = config;
}

bool CommandRouter::send_command(std::string device, std::string action) {
    if (!config_ || !gateway_) {
        ESP_LOGE(TAG, "Router not initialized");
        return false;
    }

    BLEAction act;
    
    if (config_->get_action(device, action, act)) {
        ESP_LOGI(TAG, "COMMAND FOUND:%s.%s", device.c_str(), action.c_str());

        std::string packets;
        for (size_t i = 0; i < act.packets.size(); i++) {
            if (i > 0) packets += "|";
            packets += act.packets[i];
        }

        // 调用 gateway 的 send_hex 发送组装好的多包 HEX
        gateway_->send_hex(packets);
        return true;
    }

    ESP_LOGW(TAG, "device command not found:%s.%s", device.c_str(), action.c_str());
    return false;
}

} // namespace ble_gateway
} // namespace esphome
