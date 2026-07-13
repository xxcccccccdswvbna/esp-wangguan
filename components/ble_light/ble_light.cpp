#include "ble_light.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_light {

static const char *TAG = "ble_light";

// 告诉 HA 这个灯支持什么功能（亮度、色温）
light::LightTraits BLELight::get_traits() {
    auto traits = light::LightTraits();
    // 支持亮度和色温模式
    traits.set_supported_color_modes({
        light::ColorMode::BRIGHTNESS, 
        light::ColorMode::COLOR_TEMPERATURE
    });
    
    // 色温范围 (单位: mireds)
    // 153 mireds ≈ 6500K (冷白)
    // 370 mireds ≈ 2700K (暖黄)
    traits.set_min_mireds(153.0f); 
    traits.set_max_mireds(370.0f); 
    
    return traits;
}

// 当 HA 下发控制指令时触发
void BLELight::write_state(light::LightState *state) {
    if (!gateway_) {
        ESP_LOGE(TAG, "Gateway not initialized!");
        return;
    }

    // 获取 HA 传来的目标状态 (remote_values 是目标值，current_values 是渐变过程中的当前值)
    auto values = state->remote_values;
    
    bool is_on = values.is_on();
    float brightness = values.get_brightness(); // 0.0 ~ 1.0
    float color_temp = values.get_color_temperature(); // mireds (153 ~ 370)

    ESP_LOGI(TAG, "Received state: on=%d, bright=%.2f, temp=%.2f", is_on, brightness, color_temp);

    std::string action = "";

    if (!is_on) {
        // 如果是关灯，直接发 off
        action = "off";
    } else {
        // 如果是开灯，需要组合亮度和色温动作
        // 注意：米家灯通常需要先发色温，再发亮度，或者一起发。
        // 这里我们先发色温，再发亮度。
        
        std::string temp_action = map_color_temp(color_temp);
        std::string bright_action = map_brightness(brightness);

        // 先发送色温指令
        if (!temp_action.empty()) {
            std::string cmd_temp = device_id_ + "." + temp_action;
            ESP_LOGI(TAG, "Sending Color Temp: %s", cmd_temp.c_str());
            gateway_->handle_command(cmd_temp);
        }

        // 再发送亮度指令 (作为最终 action 返回，用于日志记录)
        action = bright_action;
    }

    // 发送最终动作 (如果是关灯，这里就是 "off"；如果是开灯，这里发亮度)
    if (!action.empty()) {
        std::string cmd = device_id_ + "." + action;
        ESP_LOGI(TAG, "Sending Action: %s", cmd.c_str());
        gateway_->handle_command(cmd);
    }
}

// 亮度映射算法 (0.0 ~ 1.0 映射到预设的档位)
std::string BLELight::map_brightness(float brightness) {
    if (brightness < 0.05f) return "brightness_1";
    if (brightness < 0.15f) return "brightness_1"; // 0~15% 都算 1%
    if (brightness < 0.30f) return "brightness_20";
    if (brightness < 0.45f) return "brightness_40";
    if (brightness < 0.55f) return "brightness_50";
    if (brightness < 0.70f) return "brightness_60";
    if (brightness < 0.90f) return "brightness_80";
    return "brightness_100";
}

// 色温映射算法 (mireds 映射到预设的 K 值)
// mireds 越小越冷，越大越暖
std::string BLELight::map_color_temp(float mireds) {
    if (mireds < 200.0f) return "color_6500";  // 冷白
    if (mireds < 280.0f) return "color_3500";  // 自然白
    return "color_2700";                       // 暖黄
}

} // namespace ble_light
} // namespace esphome
