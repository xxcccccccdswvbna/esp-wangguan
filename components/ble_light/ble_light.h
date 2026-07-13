#pragma once

#include "esphome/core/component.h"
#include "esphome/components/light/light_output.h"
#include "../ble_gateway/ble_gateway.h"

namespace esphome {
namespace ble_light {

class BLELight : public light::LightOutput, public Component {
public:
    // 由 YAML 配置注入的依赖
    void set_gateway(ble_gateway::BLEGateway *gateway) { gateway_ = gateway; }
    void set_device_id(const std::string &device_id) { device_id_ = device_id; }

    // ESPHome LightOutput 必须实现的接口
    light::LightTraits get_traits() override;
    void write_state(light::LightState *state) override;

protected:
    ble_gateway::BLEGateway *gateway_{nullptr};
    std::string device_id_;

    // 内部映射算法
    std::string map_brightness(float brightness);
    std::string map_color_temp(float color_temp_mireds);
};

} // namespace ble_light
} // namespace esphome
