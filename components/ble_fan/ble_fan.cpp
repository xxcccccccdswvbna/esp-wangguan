#include "ble_fan.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_fan {

static const char *TAG = "ble_fan";

// 【必须】实现空的 setup 和 loop
void BLEFan::setup() {}
void BLEFan::loop() {}

fan::FanTraits BLEFan::get_traits() {
    return fan::FanTraits(false, true, true, 6);
}

void BLEFan::control(const fan::FanCall &call) {
    if (!gateway_) return;

    bool target_state = call.get_state().value_or(this->state);
    int target_speed = call.get_speed().value_or(this->speed);
    auto target_dir = call.get_direction().value_or(this->direction);

    if (target_state == last_state_ && target_speed == last_speed_ && target_dir == last_direction_) return;
    uint32_t now = millis();
    if (now - last_send_time_ < 500) return;

    if (!target_state) {
        gateway_->handle_command(device_id_ + ".off");
    } else {
        if (!last_state_) gateway_->handle_command(device_id_ + ".on");
        if (target_dir != last_direction_) {
            gateway_->handle_command(device_id_ + (target_dir == fan::FanDirection::FORWARD ? ".forward" : ".reverse"));
        }
        if (target_speed != last_speed_) {
            gateway_->handle_command(device_id_ + ".speed_" + std::to_string(target_speed));
        }
    }

    auto state_call = this->make_call();
    state_call.set_state(target_state).set_speed(target_speed).set_direction(target_dir).perform();

    last_state_ = target_state;
    last_speed_ = target_speed;
    last_direction_ = target_dir;
    last_send_time_ = now;
}

} // namespace ble_fan
} // namespace esphome
