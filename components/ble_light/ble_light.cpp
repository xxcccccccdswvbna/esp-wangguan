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

    // 构建当前期望的动作签名
    std::string current_sig = target_on ? (target_bright_action + "+" + target_temp_action) : "OFF";

    bool need_update = false;
    if (last_sent_signature_.empty()) {
        need_update = true;
    } else if (current_sig != last_sent_signature_) {
        need_update = true;
    }

    const uint32_t now = millis();
    if (!need_update) {
        // 2秒防死锁
        if (now - last_send_time_ > 2000) {
            need_update = true;
        } else {
            return;
        }
    }

    if (now - last_send_time_ < THROTTLE_MS) return;

    ESP_LOGI(TAG, "Executing: sig=%s", current_sig.c_str());

    if (!target_on) {
        // 关灯：只发 off
        gateway_->send_command(device_id_, "off");
    } else {
        // 🔥 核心修复：开灯时，无脑打包发送 on + brightness + color
        // 利用智能队列，这三个指令会依次排队发送，确保设备100%被唤醒
        gateway_->send_command(device_id_, "on");
        
        if (target_bright_action != "brightness_1") {
            gateway_->send_command(device_id_, target_bright_action);
        }
        if (target_temp_action != "color_6500") {
            gateway_->send_command(device_id_, target_temp_action);
        }
    }

    last_sent_signature_ = current_sig;
    last_send_time_ = now;
}

// 就近匹配算法：亮度
std::string BLELight::map_brightness(float brightness) {
    const float levels[] = {0.01f, 0.20f, 0.40f, 0.50f, 0.60f, 0.80f, 1.00f};
    const char* actions[] = {"brightness_1", "brightness_20", "brightness_40", 
                             "brightness_50", "brightness_60", "brightness_80", "brightness_100"};
    const int num_levels = sizeof(levels) / sizeof(levels[0]);
    float min_diff = 999.0f; int closest_idx = 0;
    for (int i = 0; i < num_levels; i++) {
        float diff = std::abs(brightness - levels[i]);
        if (diff < min_diff) { min_diff = diff; closest_idx = i; }
    }
    return actions[closest_idx];
}

// 就近匹配算法：色温
std::string BLELight::map_color_temp(float mireds) {
    const float levels[] = {370.0f, 285.0f, 153.0f};
    const char* actions[] = {"color_2700", "color_3500", "color_6500"};
    const int num_levels = sizeof(levels) / sizeof(levels[0]);
    float min_diff = 999.0f; int closest_idx = 0;
    for (int i = 0; i < num_levels; i++) {
        float diff = std::abs(mireds - levels[i]);
        if (diff < min_diff) { min_diff = diff; closest_idx = i; }
    }
    return actions[closest_idx];
}

}  // namespace ble_light
}  // namespace esphome
