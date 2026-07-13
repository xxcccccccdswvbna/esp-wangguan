#include "ble_fan.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_fan {

static const char *TAG = "ble_fan";

// 【修正】在这里实现空的 setup 和 loop
void BLEFan::setup() {
    // 初始化逻辑（保持为空）
}

void BLEFan::loop() {
    // 循环逻辑（保持为空）
}

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

    // 更新 HA 状态
    auto state_call = this->make_call();
    state_call.set_state(target_state);
    state_call.set_speed(target_speed);
    state_call.set_direction(target_dir);
    state_call.perform();

    last_state_ = target_state;
    last_speed_ = target_speed;
    last_direction_ = target_dir;
    last_send_time_ = now;
}

// 【修正】必须加上 BLEFan:: 作用域限定符
void BLEFan::update_from_ble(bool is_on, int speed, bool is_forward) {
    // 状态去重
    auto current_dir = is_forward ? fan::FanDirection::FORWARD : fan::FanDirection::REVERSE;
    if (this->state == is_on && this->speed == speed && this->direction == current_dir) {
        return;
    }

    ESP_LOGI(TAG, "Sync from BLE: on=%d, speed=%d, dir=%d", is_on, speed, (int)current_dir);

    this->state = is_on;
    this->speed = speed;
    this->direction = current_dir;
    
    // 直接发布状态给 HA，不会触发 control()
    this->publish_state();
}

} // namespace ble_fan
} // namespace esphome
