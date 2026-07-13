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
    ble_gateway::BLEGateway *gateway_{nullptr};
    std::string device_id_;

    // 映射算法
    std::string map_brightness(float brightness);
    std::string map_color_temp(float color_temp_mireds);

    // 【新增】状态缓存与防抖变量
    uint32_t last_send_time_{0};           // 上次发送 BLE 包的时间
    std::string last_brightness_action_;   // 上次发送的亮度指令 (如 "brightness_50")
    std::string last_color_temp_action_;   // 上次发送的色温指令 (如 "color_3500")
    bool is_currently_on_{false};          // 当前记录的开关状态
};

} // namespace ble_light
} // namespace esphome
