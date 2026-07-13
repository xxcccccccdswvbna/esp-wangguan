#pragma once

#include "esphome/components/light/light_output.h"
#include "../ble_gateway/ble_gateway.h"

namespace esphome {
namespace ble_light {

// 【修改】只继承 LightOutput，移除 Component
class BLELight : public light::LightOutput {
public:
    void set_gateway(ble_gateway::BLEGateway *gateway) { gateway_ = gateway; }
    void set_device_id(const std::string &device_id) { device_id_ = device_id; }

    light::LightTraits get_traits() override;
    void write_state(light::LightState *state) override;

protected:
    ble_gateway::BLEGateway *gateway_{nullptr};
    std::string device_id_;

    std::string map_brightness(float brightness);
    std::string map_color_temp(float color_temp_mireds);
};

} // namespace ble_light
} // namespace esphome
