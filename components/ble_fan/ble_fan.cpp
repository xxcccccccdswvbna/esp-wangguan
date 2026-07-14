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

    const bool              target_state = call.get_state().value_or(this->state);
    const int               target_speed = call.get_speed().value_or(this->speed);
    const fan::FanDirection target_dir   = call.get_direction().value_or(this->direction);

    // 状态缓存: 完全一致直接返回
    if (target_state == last_state_ &&
        target_speed == last_speed_ &&
        target_dir   == last_direction_) {
        return;
    }

    // 节流: 拒绝过于密集的连发
    const uint32_t now = millis();
    if (now - last_send_time_ < THROTTLE_MS) return;

    ESP_LOGI(TAG, "Fan control: state=%d, speed=%d, dir=%d",
             target_state, target_speed, (int) target_dir);

    if (!target_state) {
        gateway_->send_command(device_id_, "off");
    } else {
        if (!last_state_) {
            gateway_->send_command(device_id_, "on");
        }
        if (target_dir != last_direction_) {
            gateway_->send_command(device_id_,
                target_dir == fan::FanDirection::FORWARD ? "forward" : "reverse");
        }
        if (target_speed != last_speed_) {
            gateway_->send_command(device_id_,
                std::string("speed_") + std::to_string(target_speed));
        }
    }

    // 直接更新基类状态并发布 (不要用 make_call().perform(), 会死循环)
    this->state     = target_state;
    this->speed     = target_speed;
    this->direction = target_dir;
    this->publish_state();

    // 更新本地缓存
    last_state_     = target_state;
    last_speed_     = target_speed;
    last_direction_ = target_dir;
    last_send_time_ = now;
}

}  // namespace ble_fan
}  // namespace esphome
