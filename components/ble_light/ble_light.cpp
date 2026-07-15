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

    // 🔥 核心修复：构建当前期望的动作组合字符串，与上次发送的进行对比
    // 如果目标是“关”，我们构造一个特殊的 "off" 标记
    std::string current_action_signature = target_on ? (target_bright_action + "+" + target_temp_action) : "OFF";
    
    bool need_update = false;
    
    // 1. 如果是第一次启动（缓存为空），强制更新
    if (last_sent_signature_.empty()) {
        need_update = true;
        ESP_LOGI(TAG, "First-time sync: forcing update.");
    } 
    // 2. 如果动作签名变了，必须更新
    else if (current_action_signature != last_sent_signature_) {
        need_update = true;
    }

    if (!need_update) {
        ESP_LOGD(TAG, "State unchanged, skipping. (sig: %s)", current_action_signature.c_str());
        return;
    }

    // 节流保护
    const uint32_t now = millis();
    if (now - last_send_time_ < THROTTLE_MS) {
        ESP_LOGD(TAG, "Throttled, skipping.");
        return;
    }

    ESP_LOGI(TAG, "Executing: sig=%s", current_action_signature.c_str());

    if (!target_on) {
        // 关灯：只发 off
        gateway_->send_command(device_id_, "off");
    } else {
        // 开灯或调节：
        // 如果上次是关，或者这是第一次，先发送 on 唤醒
        if (last_sent_signature_ == "OFF" || last_sent_signature_.empty()) {
            gateway_->send_command(device_id_, "on");
            // 利用智能队列追加亮度和色温
            if (target_bright_action != "brightness_1") {
                gateway_->send_command(device_id_, target_bright_action);
            }
            if (target_temp_action != "color_6500") {
                gateway_->send_command(device_id_, target_temp_action);
            }
        } else {
            // 已经是开着的：只发变化了的参数
            // 注意：由于我们用了签名对比，这里可以直接发对应的动作
            if (target_temp_action != "color_6500") { // 简单判断，防止重复发默认值
                 gateway_->send_command(device_id_, target_temp_action);
            }
            if (target_bright_action != "brightness_1") {
                 gateway_->send_command(device_id_, target_bright_action);
            }
        }
    }

    // 🔥 更新签名缓存
    last_sent_signature_ = current_action_signature;
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
