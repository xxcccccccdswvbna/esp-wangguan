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
            // 从关 -> 开，先发 on，再延迟发 brightness/color
            gateway_->send_command(device_id_, "on");
            
            // 标记延迟发送（200ms 后发送 brightness/color）
            pending_brightness_ = target_bright_action;
            pending_color_ = target_temp_action;
            pending_send_time_ = now + 200;
            
            ESP_LOGD(TAG, "Scheduled brightness/color send in 200ms");
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

void BLELight::loop() {
    if (pending_send_time_ > 0 && millis() >= pending_send_time_) {
        if (!pending_brightness_.empty()) {
            gateway_->send_command(device_id_, pending_brightness_);
            ESP_LOGD(TAG, "Delayed send: %s", pending_brightness_.c_str());
            pending_brightness_ = "";
        }
        if (!pending_color_.empty()) {
            gateway_->send_command(device_id_, pending_color_);
            ESP_LOGD(TAG, "Delayed send: %s", pending_color_.c_str());
            pending_color_ = "";
        }
        pending_send_time_ = 0;
    }
}

// 🔥 核心修复：就近匹配算法，将连续值映射到最近的固定档位
std::string BLELight::map_brightness(float brightness) {
    // 定义固定的亮度档位（0.0 - 1.0）
    const float levels[] = {0.01f, 0.20f, 0.40f, 0.50f, 0.60f, 0.80f, 1.00f};
    const char* actions[] = {"brightness_1", "brightness_20", "brightness_40", 
                             "brightness_50", "brightness_60", "brightness_80", "brightness_100"};
    const int num_levels = sizeof(levels) / sizeof(levels[0]);
    
    // 找到距离最近的档位
    float min_diff = 999.0f;
    int closest_idx = 0;
    
    for (int i = 0; i < num_levels; i++) {
        float diff = std::abs(brightness - levels[i]);
        if (diff < min_diff) {
            min_diff = diff;
            closest_idx = i;
        }
    }
    
    ESP_LOGD(TAG, "Brightness %.2f -> mapped to %s (%.0f%%)", 
             brightness, actions[closest_idx], levels[closest_idx] * 100);
    
    return actions[closest_idx];
}

// 🔥 核心修复：就近匹配算法，将连续色温映射到最近的固定档位
std::string BLELight::map_color_temp(float mireds) {
    // 定义固定的色温档位（mireds）
    // 2700K = 370 mireds, 3500K = 285 mireds, 6500K = 153 mireds
    const float levels[] = {370.0f, 285.0f, 153.0f};
    const char* actions[] = {"color_2700", "color_3500", "color_6500"};
    const int num_levels = sizeof(levels) / sizeof(levels[0]);
    
    // 找到距离最近的档位
    float min_diff = 999.0f;
    int closest_idx = 0;
    
    for (int i = 0; i < num_levels; i++) {
        float diff = std::abs(mireds - levels[i]);
        if (diff < min_diff) {
            min_diff = diff;
            closest_idx = i;
        }
    }
    
    ESP_LOGD(TAG, "Color temp %.1f mireds -> mapped to %s (%.0f mireds)", 
             mireds, actions[closest_idx], levels[closest_idx]);
    
    return actions[closest_idx];
}

}  // namespace ble_light
}  // namespace esphome
