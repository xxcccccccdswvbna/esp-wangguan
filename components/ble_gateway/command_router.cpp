#include "command_router.h"
#include "ble_gateway.h"
#include "config_manager.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_gateway {

static const char *TAG = "command_router";

bool CommandRouter::send_command(const std::string &device,
                                 const std::string &action) {
    if (!config_ || !gateway_) {
        ESP_LOGE(TAG, "Router not initialized");
        return false;
    }

    // 零拷贝查找动作
    const BLEAction *act = config_->find_action(device, action);
    if (!act) {
        ESP_LOGW(TAG, "device command not found: %s.%s",
                 device.c_str(), action.c_str());
        return false;
    }

    ESP_LOGI(TAG, "COMMAND FOUND: %s.%s", device.c_str(), action.c_str());
    // 统一交由 Gateway 的队列处理
    gateway_->enqueue_packets(act->packets);
    return true;
}

}  // namespace ble_gateway
}  // namespace esphome
