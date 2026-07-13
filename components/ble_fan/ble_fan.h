#pragma once

// 【修正】不需要包含 component.h
#include "esphome/components/fan/fan.h"
#include "../ble_gateway/ble_gateway.h"

namespace esphome {
namespace ble_fan {

// 【核心】只继承 fan::Fan，绝对不要加 public Component
class BLEFan : public fan::Fan {
public:
    void set_gateway(ble_gateway::BLEGateway *gateway) { gateway_ = gateway; }
    void set_device_id(const std::string &device_id) { device_id_ = device_id; }

    fan::FanTraits get_traits() override;
    void control(const fan::FanCall &call) override;

protected:
    ble_gateway::BLEGateway *gateway_{nullptr};
    std::string device_id_;

    uint32_t last_send_time_{0};
    bool last_state_{false};
    int last_speed_{0};
    fan::FanDirection last_direction_{fan::FanDirection::FORWARD};
};

} // namespace ble_fan
} // namespace esphome
