#include "ble_fan.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_fan {

static const char *TAG = "ble_fan";

void BLEFan::setup() {}
void BLEFan::loop() {}

fan::FanTraits BLEFan::get_traits() {
    return fan::FanTraits(false, true, true, 6);
}

void BLEFan::control(const fan::FanCall &call) {
    if (!gateway_) {
        ESP_LOGE(TAG, "Gateway not initialized!");
        return;
    }

    bool target_state = call.get_state().value_or(this->state);
    int target_speed = call.get_speed().value_or(this->speed);
    auto target_dir = call.get_direction().value_or(this->direction);

    // 状态缓存 & 指令去重
    if (target_state == last_state_ && 
        target_speed == last_speed_ && 
        target_dir == last_direction_) {
        return; 
    }

    uint32_t now = millis();
    if (now - last_send_time_ < 500) { 
        return; 
    }

    ESP_LOGI(TAG, "Fan control: state=%d, speed=%d, dir=%d", target_state, target_speed, (int)target_dir);

    if (!target_state) {
        gateway_->handle_command(device_id_ + ".off");
    } else {
        if (!last_state_) {
            gateway_->handle_command(device_id_ + ".on");
        }
        if (target_dir != last_direction_) {
            if (target_dir == fan::FanDirection::FORWARD) {
                gateway_->handle_command(device_id_ + ".forward");
            } else {
                gateway_->handle_command(device_id_ + ".reverse");
            }
        }
        if (target_speed != last_speed_) {
            std::string speed_cmd = device_id_ + ".speed_" + std::to_string(target_speed);
            gateway_->handle_command(speed_cmd);
        }
    }

    // ==========================================
    // 【终极修正】：直接更新基类状态并发布！
    // 绝对不要使用 make_call().perform()，那会导致无限死循环卡死 API！
    // ==========================================
    this->state = target_state;
    this->speed = target_speed;
    this->direction = target_dir;
    
    // 通知 Home Assistant 状态已更新
    this->publish_state();

    // 更新本地缓存
    last_state_ = target_state;
    last_speed_ = target_speed;
    last_direction_ = target_dir;
    last_send_time_ = now;
}

} // namespace ble_fan
} // namespace esphome
