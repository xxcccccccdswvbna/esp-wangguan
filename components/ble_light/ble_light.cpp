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

    // 🔥 核心修复：不再依赖 is_currently_on_ 猜测，而是对比 HA 目标状态与上次实际发送的状态
    bool need_update = false;
    if (target_on != last_sent_on_) need_update = true;
    if (target_bright_action != last_sent_brightness_) need_update = true;
    if (target_temp_action != last_sent_color_) need_update = true;

    if (!need_update) {
        ESP_LOGD(TAG, "State unchanged, skipping.");
        return;
    }

    // 节流保护
    const uint32_t now = millis();
    if (now - last_send_time_ < THROTTLE_MS) {
        ESP_LOGD(TAG, "Throttled, skipping.");
        return;
    }

    ESP_LOGI(TAG, "State: on=%d bright=%.2f temp=%.2f -> mapped: %s, %s",
             target_on, brightness, color_temp, target_bright_action.c_str(), target_temp_action.c_str());

    if (!target_on) {
        // 关灯：只发 off
        gateway_->send_command(device_id_, "off");
    } else {
        // 开灯或调节：
        if (!last_sent_on_) {
            // 从关 -> 开：利用智能队列，连续发送 on 和 brightness/color
            gateway_->send_command(device_id_, "on");
            if (target_bright_action != "brightness_1") {
                gateway_->send_command(device_id_, target_bright_action);
            }
            if (target_temp_action != "color_6500") {
                gateway_->send_command(device_id_, target_temp_action);
            }
        } else {
            // 已经是开着的：只发变化了的参数
            if (target_temp_action != last_sent_color_) {
                gateway_->send_command(device_id_, target_temp_action);
            }
            if (target_bright_action != last_sent_brightness_) {
                gateway_->send_command(device_id_, target_bright_action);
            }
        }
    }

    // 🔥 更新“上次实际发送”的缓存，而不是猜测的状态
    last_sent_on_        = target_on;
    last_sent_brightness_= target_bright_action;
    last_sent_color_     = target_temp_action;
    last_send_time_      = now;
}

// 就近匹配算法：亮度
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

// 就近匹配算法：色温
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
