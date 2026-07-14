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

    // 完全无变化直接跳过
    if (target_on == is_currently_on_) {
        if (!target_on ||
            (target_bright_action == last_brightness_action_ &&
             target_temp_action   == last_color_temp_action_)) {
            ESP_LOGD(TAG, "State unchanged, skipping.");
            return;
        }
    }

    // 节流
    const uint32_t now = millis();
    if (now - last_send_time_ < THROTTLE_MS) {
        ESP_LOGD(TAG, "Throttled, skipping.");
        return;
    }

    ESP_LOGI(TAG, "State: on=%d bright=%.2f temp=%.2f (was_on=%d)",
             target_on, brightness, color_temp, is_currently_on_);

    if (!target_on) {
        // 关灯
        gateway_->send_command(device_id_, "off");
    } else if (!is_currently_on_) {
        // off → on: 只发 on, 保留灯自身记忆的亮度色温
        gateway_->send_command(device_id_, "on");
    } else {
        // 已开着: 只发用户真正改变的量
        if (target_temp_action != last_color_temp_action_) {
            gateway_->send_command(device_id_, target_temp_action);
        }
        if (target_bright_action != last_brightness_action_) {
            gateway_->send_command(device_id_, target_bright_action);
        }
    }

    // 更新缓存
    is_currently_on_        = target_on;
    last_brightness_action_ = target_bright_action;
    last_color_temp_action_ = target_temp_action;
    last_send_time_         = now;
}

// 亮度 (0.0~1.0) → 档位动作名
std::string BLELight::map_brightness(float brightness) {
    if (brightness < 0.15f) return "brightness_1";
    if (brightness < 0.30f) return "brightness_20";
    if (brightness < 0.45f) return "brightness_40";
    if (brightness < 0.55f) return "brightness_50";
    if (brightness < 0.70f) return "brightness_60";
    if (brightness < 0.90f) return "brightness_80";
    return "brightness_100";
}

// 色温 (mireds) → 档位动作名
std::string BLELight::map_color_temp(float mireds) {
    if (mireds < 200.0f) return "color_6500";  // 冷白
    if (mireds < 280.0f) return "color_3500";  // 自然白
    return "color_2700";                       // 暖黄
}

}  // namespace ble_light
}  // namespace esphome
