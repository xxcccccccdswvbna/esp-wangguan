#pragma once

#include "esphome/core/component.h"
#include "esphome/components/fan/fan.h"
#include "../ble_gateway/ble_gateway.h"

namespace esphome {
namespace ble_fan {

class BLEFan : public fan::Fan, public Component {
public:
    void setup() override;
    void loop() override;

    void set_gateway(ble_gateway::BLEGateway *gateway) { gateway_ = gateway; }
    void set_device_id(const std::string &device_id) { device_id_ = device_id; }

    fan::FanTraits get_traits() override;
    void control(const fan::FanCall &call) override;

protected:
    // 与 BLELight 对齐的节流窗口
    static constexpr uint32_t THROTTLE_MS = 500;

    ble_gateway::BLEGateway *gateway_{nullptr};
    std::string device_id_;

    // 状态缓存 (用于去重)
    uint32_t          last_send_time_{0};
    bool              last_state_{false};
    int               last_speed_{0};
    fan::FanDirection last_direction_{fan::FanDirection::FORWARD};
};

}  // namespace ble_fan
}  // namespace esphome
