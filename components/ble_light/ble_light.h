#pragma once

#include "esphome/components/light/light_output.h"
#include "../ble_gateway/ble_gateway.h"

namespace esphome {
namespace ble_light {

class BLELight : public light::LightOutput {
public:
    void set_gateway(ble_gateway::BLEGateway *gateway) { gateway_ = gateway; }
    void set_device_id(const std::string &device_id) { device_id_ = device_id; }

    light::LightTraits get_traits() override;
    void write_state(light::LightState *state) override;

protected:
    // 节流窗口 (与 BLEFan 对齐)
    static constexpr uint32_t THROTTLE_MS = 500;

    // 色温边界 (mireds)
    static constexpr float MIREDS_MIN = 153.0f;  // 6500K
    static constexpr float MIREDS_MAX = 370.0f;  // 2700K

    ble_gateway::BLEGateway *gateway_{nullptr};
    std::string device_id_;

    // 档位映射
    static std::string map_brightness(float brightness);
    static std::string map_color_temp(float mireds);

    // 状态缓存
    uint32_t    last_send_time_{0};
    std::string last_brightness_action_;
    std::string last_color_temp_action_;
    bool        is_currently_on_{false};
};

}  // namespace ble_light
}  // namespace esphome
