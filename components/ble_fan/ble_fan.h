#pragma once

#include "esphome/core/component.h"
#include "esphome/components/fan/fan.h"
#include "../ble_gateway/ble_gateway.h"

namespace esphome {
namespace ble_fan {

class BLEFan : public fan::Fan {
public:
    // 【必须】显式声明 setup 和 loop，保证虚函数表完整
    void setup() override;
    void loop() override;

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
