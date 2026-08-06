#include "ble_fan.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_fan {

static const char *TAG = "ble_fan";

void BLEFan::setup() { ESP_LOGI(TAG, "BLE Fan setup"); }
void BLEFan::loop() {}

fan::FanTraits BLEFan::get_traits() {
    return fan::FanTraits(false, true, true, 6); 
}

void BLEFan::control(const fan::FanCall &call) {
    if (!gateway_) return;
    const auto *dev = gateway_->get_device(device_id_);
    if (!dev) return;

    const bool target_on = call.get_state().has_value() ? *call.get_state() : this->state;
    const int target_speed = call.get_speed().has_value() ? *call.get_speed() : this->speed;
    const fan::FanDirection target_dir = call.get_direction().has_value() ? *call.get_direction() : this->direction;

    const uint32_t now = millis();
    if (now - last_send_time_ < THROTTLE_MS) return;
    last_send_time_ = now;

    if (dev->protocol == "MIDEA") {
        if (!target_on) {
            gateway_->send_midea_command(dev->mac, 0, {0x0B}); 
        } else {
            if (!this->state) gateway_->send_midea_command(dev->mac, 0, {0x09}); 
            
            if (target_speed > 0) {
                uint8_t speed_cmd = 0x19;
                switch(target_speed) {
                    case 1: speed_cmd = 0x19; break; case 2: speed_cmd = 0x1A; break;
                    case 3: speed_cmd = 0x81; break; case 4: speed_cmd = 0x88; break;
                    case 5: speed_cmd = 0x85; break; case 6: speed_cmd = 0x86; break;
                }
                gateway_->send_midea_command_delayed(dev->mac, 0, {speed_cmd}, 200);
            }
            if (target_dir != this->direction) {
                gateway_->send_midea_command_delayed(dev->mac, 0, {0x1C}, 400);
            }
        }
        this->state = target_on; this->speed = target_speed; this->direction = target_dir; 
        this->publish_state();
        return;
    }

    // 原有 8153/134D 逻辑
    std::string action_to_send = "";
    if (!target_on) {
        if (this->state) action_to_send = "off";
    } else {
        if (!this->state) {
            if (target_speed > 0) action_to_send = "speed_" + std::to_string(target_speed);
            else action_to_send = "on";
        } else {
            if (target_dir != this->direction) action_to_send = (target_dir == fan::FanDirection::REVERSE) ? "reverse" : "forward";
            else if (target_speed != this->speed) action_to_send = "speed_" + std::to_string(target_speed);
        }
    }
    if (!action_to_send.empty()) gateway_->send_command(device_id_, action_to_send);

    this->state = target_on; this->speed = target_speed; this->direction = target_dir; 
    last_send_time_ = now;
    this->publish_state();
}

}  // namespace ble_fan
}  // namespace esphome
