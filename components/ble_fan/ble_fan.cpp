#include "ble_fan.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_fan {

static const char *TAG = "ble_fan";

void BLEFan::setup() {
    ESP_LOGI(TAG, "BLE Fan setup");
}

// 🔥 修复 1：移除了 dump_config() 的实现，因为 .h 中没有声明它

fan::FanTraits BLEFan::get_traits() {
    // 参数依次为：支持摇摆(false), 支持方向(true), 支持速度(true), 速度档位数量(6)
    return fan::FanTraits(false, true, true, 6); 
}

void BLEFan::control(const fan::FanCall &call) {
    if (!gateway_) {
        ESP_LOGE(TAG, "Gateway not initialized!");
        return;
    }

    // 获取目标状态
    const bool target_on = call.get_state().has_value() ? *call.get_state() : this->state;
    const int target_speed = call.get_speed().has_value() ? *call.get_speed() : this->speed;
    
    // 🔥 修复 2：direction 是 FanDirection 枚举类型，不再是 bool
    const fan::FanDirection target_dir = call.get_direction().has_value() ? *call.get_direction() : this->direction;

    // 节流保护
    const uint32_t now = millis();
    if (now - last_send_time_ < THROTTLE_MS) {
        ESP_LOGD(TAG, "Throttled, skipping.");
        return;
    }

    ESP_LOGI(TAG, "Fan control: state=%d, speed=%d, dir=%d (was: state=%d, speed=%d, dir=%d)",
             target_on, target_speed, target_dir, this->state, this->speed, this->direction);

    // 智能单选，只发一个最核心的指令
    std::string action_to_send = "";

    if (!target_on) {
        // 关风扇：只发 off
        if (this->state) {
            action_to_send = "off";
        }
    } else {
        // 开风扇或调节：
        if (!this->state) {
            // 从关 -> 开：优先发 speed_X（包含开+速度），如果没有速度则发 on
            if (target_speed > 0) {
                action_to_send = "speed_" + std::to_string(target_speed);
            } else {
                action_to_send = "on";
            }
        } else {
            // 已经是开着的：只发变化了的参数
            // 🔥 修复 3：使用枚举类型进行比较
            if (target_dir != this->direction) {
                action_to_send = (target_dir == fan::FAN_DIRECTION_REVERSE) ? "reverse" : "forward";
            } else if (target_speed != this->speed) {
                action_to_send = "speed_" + std::to_string(target_speed);
            }
        }
    }

    // 执行发送
    if (!action_to_send.empty()) {
        gateway_->send_command(device_id_, action_to_send);
    }

    // 更新状态
    this->state = target_on;
    this->speed = target_speed;
    // 🔥 修复 4：赋值给 this->direction 时，使用正确的枚举类型
    this->direction = target_dir; 
    last_send_time_ = now;

    this->publish_state();
}

}  // namespace ble_fan
}  // namespace esphome
