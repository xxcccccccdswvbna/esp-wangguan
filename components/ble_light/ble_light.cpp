#include "ble_light.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_light {

static const char *TAG = "ble_light";

// 告诉 HA 这个灯支持什么功能
light::LightTraits BLELight::get_traits() {
    auto traits = light::LightTraits();
    traits.set_supported_color_modes({
        light::ColorMode::BRIGHTNESS, 
        light::ColorMode::COLOR_TEMPERATURE
    });
    traits.set_min_mireds(153.0f); // 6500K
    traits.set_max_mireds(370.0f); // 2700K
    return traits;
}

// 当 HA 下发控制指令时触发
void BLELight::write_state(light::LightState *state) {
    if (!gateway_) {
        ESP_LOGE(TAG, "Gateway not initialized!");
        return;
    }

    auto values = state->remote_values;
    bool target_on = values.is_on();
    float brightness = values.get_brightness();
    float color_temp = values.get_color_temperature();

    // 1. 计算本次需要发送的指令
    std::string target_bright_action = map_brightness(brightness);
    std::string target_temp_action = map_color_temp(color_temp);

    // ==========================================
    // 【核心优化 1】：状态缓存 & 指令去重
    // ==========================================
    // 如果开关状态没变，且(灯是关的，或者 亮度和色温指令都没变)，则直接跳过！
    if (target_on == is_currently_on_) {
        if (!target_on || (target_bright_action == last_brightness_action_ && 
                           target_temp_action == last_color_temp_action_)) {
            ESP_LOGD(TAG, "State unchanged, skipping BLE send.");
            return; // 绝不重发相同的指令
        }
    }

    // ==========================================
    // 【核心优化 2】：时间节流 (防抖)
    // ==========================================
    // 限制最小发送间隔为 500ms，防止拖动滑块时 BLE 队列爆炸
    uint32_t now = millis();
    if (now - last_send_time_ < 500) { 
        ESP_LOGD(TAG, "Throttled: sending too fast, skipping.");
        return; 
    }

    ESP_LOGI(TAG, "Received state: on=%d, bright=%.2f, temp=%.2f", target_on, brightness, color_temp);

    // ==========================================
    // 执行发送逻辑
    // ==========================================
    if (!target_on) {
        // 关灯
        std::string cmd = device_id_ + ".off";
        ESP_LOGI(TAG, "Sending Action: %s", cmd.c_str());
        gateway_->handle_command(cmd);
    } else {
        // 开灯：先发色温，再发亮度
        if (target_temp_action != last_color_temp_action_ || !is_currently_on_) {
            std::string cmd_temp = device_id_ + "." + target_temp_action;
            ESP_LOGI(TAG, "Sending Color Temp: %s", cmd_temp.c_str());
            gateway_->handle_command(cmd_temp);
        }

        if (target_bright_action != last_brightness_action_ || !is_currently_on_) {
            std::string cmd_bright = device_id_ + "." + target_bright_action;
            ESP_LOGI(TAG, "Sending Action: %s", cmd_bright.c_str());
            gateway_->handle_command(cmd_bright);
        }
    }

    // ==========================================
    // 【核心优化 3】：更新状态缓存
    // ==========================================
    is_currently_on_ = target_on;
    last_brightness_action_ = target_bright_action;
    last_color_temp_action_ = target_temp_action;
    last_send_time_ = now; // 记录本次发送时间
}

// 亮度映射算法 (0.0 ~ 1.0 映射到预设的档位)
std::string BLELight::map_brightness(float brightness) {
    if (brightness < 0.05f) return "brightness_1";
    if (brightness < 0.15f) return "brightness_1"; 
    if (brightness < 0.30f) return "brightness_20";
    if (brightness < 0.45f) return "brightness_40";
    if (brightness < 0.55f) return "brightness_50";
    if (brightness < 0.70f) return "brightness_60";
    if (brightness < 0.90f) return "brightness_80";
    return "brightness_100";
}

// 色温映射算法 (mireds 映射到预设的 K 值)
std::string BLELight::map_color_temp(float mireds) {
    if (mireds < 200.0f) return "color_6500";  // 冷白
    if (mireds < 280.0f) return "color_3500";  // 自然白
    return "color_2700";                       // 暖黄
}

} // namespace ble_light
} // namespace esphome
