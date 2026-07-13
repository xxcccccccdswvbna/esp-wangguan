#pragma once

#include "esphome/core/component.h"
#include "esphome/components/fan/fan.h"
#include "../ble_gateway/ble_gateway.h"

namespace esphome {
namespace ble_fan {

class BLEFan : public fan::Fan, public Component {
public:
    void set_gateway(ble_gateway::BLEGateway *gateway) { gateway_ = gateway; }
    void set_device_id(const std::string &device_id) { device_id_ = device_id; }

    // 告诉 HA 这个风扇支持什么功能
    fan::FanTraits get_traits() override;
    
    // 当 HA 下发控制指令时触发
    void control(const fan::FanCall &call) override;

protected:
    ble_gateway::BLEGateway *gateway_{nullptr};
    std::string device_id_;

    // 状态缓存与防抖
    uint32_t last_send_time_{0};
    bool last_state_{false};
    int last_speed_{0};
    fan::FanDirection last_direction_{fan::FanDirection::FORWARD};
};

} // namespace ble_fan
} // namespace esphome
