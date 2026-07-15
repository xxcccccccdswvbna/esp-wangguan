#include "ble_light.h"
#include "esphome/core/log.h"
#include <cmath>

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

    // 节流保护
    const uint32_t now = millis();
    if (now - last_send_time_ < THROTTLE_MS) {
        ESP_LOGD(TAG, "Throttled, skipping.");
        return;
    }

    ESP_LOGI(TAG, "State: on=%d bright=%.2f temp=%.2f (was_on=%d) -> mapped: %s, %s",
             target_on, brightness, color_temp, is_currently_on_,
             target_bright_action.c_str(), target_temp_action.c_str());

    if (!target_on) {
        // 关灯：只发 off
        if (is_currently_on_) {
            gateway_->send_command(device_id_, "off");
        }
    } else {
        // 开灯或调节：
        if (!is_currently_on_) {
            // 🔥 核心修复：从关 -> 开，利用智能队列，连续发送 on 和 brightness/color
            // 网关会自动将它们按顺序排队发送，不会互相覆盖！
            gateway_->send_command(device_id_, "on");
            
            // 如果亮度不是默认的 1%，则发送亮度指令
            if (target_bright_action != "brightness_1") {
                gateway_->send_command(device_id_, target_bright_action);
            }
            // 如果色温不是默认的 6500K，则发送色温指令
            if (target_temp_action != "color_6500") {
                gateway_->send_command(device_id_, target_temp_action);
            }
        } else {
            // 已经是开着的：只发变化了的参数
            if (target_temp_action != last_color_temp_action_) {
                gateway_->send_command(device_id_, target_temp_action);
            }
            if (target_bright_action != last_brightness_action_) {
                gateway_->send_command(device_id_, target_bright_action);
            }
        }
    }

    // 更新缓存
    is_currently_on_        = target_on;
    last_brightness_action_ = target_bright_action;
    last_color_temp_action_ = target_temp_action;
    last_send_time_         = now;
}

// 🔥 就近匹配算法：亮度
std::string BLELight::map_brightness(float brightness) {
    const float levels[] = {0.01f, 0.20f, 0.40f, 0.50f, 0.60f, 0.80f, 1.00f};
    const char* actions[] = {"brightness_1", "brightness_20", "brightness_40", 
                             "brightness_50", "brightness_60", "brightness_80", "brightness_100"};
    const int num_levels = sizeof(levels) / sizeof(levels[0]);
    
    float min_diff = 999.0f;
    int closest_idx = 0;
    
    for (int i = 0; i < num_levels; i++) {
        float diff = std::abs(brightness - levels[i]);
        if (diff < min_diff) {
            min_diff = diff;
            closest_idx = i;
        }
    }
    return actions[closest_idx];
}

// 🔥 就近匹配算法：色温
std::string BLELight::map_color_temp(float mireds) {
    const float levels[] = {370.0f, 285.0f, 153.0f};
    const char* actions[] = {"color_2700", "color_3500", "color_6500"};
    const int num_levels = sizeof(levels) / sizeof(levels[0]);
    
    float min_diff = 999.0f;
    int closest_idx = 0;
    
    for (int i = 0; i < num_levels; i++) {
        float diff = std::abs(mireds - levels[i]);
        if (diff < min_diff) {
            min_diff = diff;
            closest_idx = i;
        }
    }
    return actions[closest_idx];
}

}  // namespace ble_light
}  // namespace esphome
