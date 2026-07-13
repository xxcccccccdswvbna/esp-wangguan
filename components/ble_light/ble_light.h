#pragma once

#include "esphome/core/component.h"
#include "esphome/components/light/light_output.h"
#include "../ble_gateway/ble_gateway.h"

namespace esphome {
namespace ble_light {

class BLELight : public light::LightOutput, public Component {
public:
    void setup() override {} // 空实现，满足 Component 接口
    void loop() override {}

    void set_gateway(ble_gateway::BLEGateway *gateway) { gateway_ = gateway; }
    void set_device_id(const std::string &device_id) { device_id_ = device_id; }
    
    // 【新增】保存 LightState 指针，用于从 BLE 广播更新状态
    void set_state_parent(light::LightState *state) { state_parent_ = state; }

    light::LightTraits get_traits() override;
    void write_state(light::LightState *state) override;

    // 【新增】从 BLE 广播更新状态的方法
    void update_from_ble(bool is_on, float brightness, float color_temp_mireds);

protected:
    ble_gateway::BLEGateway *gateway_{nullptr};
    std::string device_id_;
    light::LightState *state_parent_{nullptr};

    uint32_t last_send_time_{0};
    std::string last_brightness_action_;
    std::string last_color_temp_action_;
    bool is_currently_on_{false};

    // 【关键】防死循环标志位
    bool ignore_next_write_{false};

    std::string map_brightness(float brightness);
    std::string map_color_temp(float color_temp_mireds);
};

} // namespace ble_light
} // namespace esphome
