#include "ble_light.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_light {

static const char *TAG = "ble_light";

light::LightTraits BLELight::get_traits() {
    light::LightTraits traits;
    traits.set_supported_color_modes({
        light::ColorMode::BRIGHTNESS,
        light::ColorMode::COLOR_TEMPERATURE,
    });
    traits.set_min_mireds(MIREDS_MIN);
    traits.set_max_mireds(MIREDS_MAX);
    return traits;
}

void BLELight::write_state(light::LightState *state) {
    if (!gateway_) {
        ESP_LOGE(TAG, "Gateway not initialized!");
        return;
    }

    const auto &values     = state->remote_values;
    const bool  target_on  = values.is_on();
    const float brightness = values.get_brightness();
    const float color_temp = values.get_color_temperature();

    const std::string target_bright_action = map_brightness(brightness);
    const std::string target_temp_action   = map_color_temp(color_temp);

    // 1. 完全无变化，直接跳过
    if (target_on == is_currently_on_) {
        if (!target_on ||
            (target_bright_action == last_brightness_action_ &&
             target_temp_action   == last_color_temp_action_)) {
            ESP_LOGD(TAG, "State unchanged, skipping.");
            return;
        }
    }

    // 2. 节流保护
    const uint32_t now = millis();
    if (now - last_send_time_ < THROTTLE_MS) {
        ESP_LOGD(TAG, "Throttled, skipping.");
        return;
    }

    ESP_LOGI(TAG, "State: on=%d bright=%.2f temp=%.2f (was_on=%d)",
             target_on, brightness, color_temp, is_currently_on_);

    // 🔥 3. 核心修复：每次只精选 1 个最核心的指令发送，确保该指令的多个包能完整发完，不被覆盖
    std::string action_to_send = "";

    if (!target_on) {
        // 【关灯】：如果当前是开着的，发送关灯指令
        if (is_currently_on_) {
            action_to_send = "off";
        }
    } else {
        // 【开灯或调节】：
        if (!is_currently_on_) {
            // 从关 -> 开：优先发送亮度或色温指令（通常这类指令本身就包含“开灯”效果）
            // 如果亮度/色温没有明显变化，则发送纯 "on" 指令
            if (target_bright_action != "brightness_1" || target_temp_action != "color_6500") {
                // 优先发亮度，因为亮度指令通常权重更高
                action_to_send = target_bright_action; 
            } else {
                action_to_send = "on";
            }
        } else {
            // 已经是开着的：检查哪个参数变了，只发送变化了的那个单独指令
            if (target_temp_action != last_color_temp_action_) {
                action_to_send = target_temp_action;
            } else if (target_bright_action != last_brightness_action_) {
                action_to_send = target_bright_action;
            }
        }
    }

    // 4. 执行发送 (此时 action_to_send 只有一个值，它的 1~2 个包会被完整放入队列并依次发完)
    if (!action_to_send.empty()) {
        gateway_->send_command(device_id_, action_to_send);
    }

    // 5. 更新本地缓存状态
    is_currently_on_        = target_on;
    last_brightness_action_ = target_bright_action;
    last_color_temp_action_ = target_temp_action;
    last_send_time_         = now;
}

std::string BLELight::map_brightness(float brightness) {
    if (brightness < 0.15f) return "brightness_1";
    if (brightness < 0.30f) return "brightness_20";
    if (brightness < 0.45f) return "brightness_40";
    if (brightness < 0.55f) return "brightness_50";
    if (brightness < 0.70f) return "brightness_60";
    if (brightness < 0.90f) return "brightness_80";
    return "brightness_100";
}

std::string BLELight::map_color_temp(float mireds) {
    if (mireds < 200.0f) return "color_6500";
    if (mireds < 280.0f) return "color_3500";
    return "color_2700";
}

}  // namespace ble_light
}  // namespace esphome