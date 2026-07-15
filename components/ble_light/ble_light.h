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

    // 🔥 核心修复：更新缓存变量名，打破 HA "未知" 状态死锁
    uint32_t    last_send_time_{0};
    bool        last_sent_on_{false};
    std::string last_sent_brightness_;
    std::string last_sent_color_;
};

}  // namespace ble_light
}  // namespace esphome
