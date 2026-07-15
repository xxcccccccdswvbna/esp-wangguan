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
    static constexpr uint32_t THROTTLE_MS = 500;
    static constexpr float MIREDS_MIN = 153.0f;
    static constexpr float MIREDS_MAX = 370.0f;

    ble_gateway::BLEGateway *gateway_{nullptr};
    std::string device_id_;

    static std::string map_brightness(float brightness);
    static std::string map_color_temp(float mireds);

    uint32_t    last_send_time_{0};
    std::string last_brightness_action_;
    std::string last_color_temp_action_;
    bool        is_currently_on_{false};
    
    // 🔥 新增：延迟发送队列
    std::string pending_brightness_;
    std::string pending_color_;
    uint32_t    pending_send_time_{0};
};

}  // namespace ble_light
}  // namespace esphome
