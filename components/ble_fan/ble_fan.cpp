#include "ble_fan.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_fan {

static const char *TAG = "ble_fan";

// 告诉 HA 这个风扇的特性
fan::FanTraits BLEFan::get_traits() {
    // 【修正】使用构造函数初始化 FanTraits
    // 参数顺序: oscillation (是否支持摇头), speed (是否支持调速), direction (是否支持正反转), supported_speed_count (支持的档位数量)
    return fan::FanTraits(false, true, true, 6);
}

// 当 HA 下发控制指令时触发
void BLEFan::control(const fan::FanCall &call) {
    if (!gateway_) {
        ESP_LOGE(TAG, "Gateway not initialized!");
        return;
    }

    // 获取目标状态
    bool target_state = call.get_state().value_or(this->state);
    int target_speed = call.get_speed().value_or(this->speed);
    auto target_dir = call.get_direction().value_or(this->direction);

    // ==========================================
    // 【核心优化】：状态缓存 & 指令去重
    // ==========================================
    if (target_state == last_state_ && 
        target_speed == last_speed_ && 
        target_dir == last_direction_) {
        ESP_LOGD(TAG, "Fan state unchanged, skipping.");
        return; 
    }

    // 节流：限制最小发送间隔为 500ms
    uint32_t now = millis();
    if (now - last_send_time_ < 500) { 
        ESP_LOGD(TAG, "Throttled: sending too fast.");
        return; 
    }

    ESP_LOGI(TAG, "Fan control: state=%d, speed=%d, dir=%d", target_state, target_speed, (int)target_dir);

    // ==========================================
    // 执行发送逻辑
    // ==========================================
    if (!target_state) {
        // 1. 如果是关，直接发 off
        gateway_->handle_command(device_id_ + ".off");
    } else {
        // 2. 如果是开
        // 如果之前是关的，先发 on
        if (!last_state_) {
            gateway_->handle_command(device_id_ + ".on");
        }

        // 处理方向变化
        if (target_dir != last_direction_) {
            if (target_dir == fan::FanDirection::FORWARD) {
                gateway_->handle_command(device_id_ + ".forward");
            } else {
                gateway_->handle_command(device_id_ + ".reverse");
            }
        }

        // 处理速度变化 (1-6)
        if (target_speed != last_speed_) {
            std::string speed_cmd = device_id_ + ".speed_" + std::to_string(target_speed);
            gateway_->handle_command(speed_cmd);
        }
    }

    // ==========================================
    // 更新 HA 状态 & 本地缓存
    // ==========================================
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

} // namespace ble_fan
} // namespace esphome
