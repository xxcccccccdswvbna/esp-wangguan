#include "ble_light.h"
#include "esphome/core/log.h"

namespace esphome {
namespace ble_light {

static const char *TAG = "ble_light";

light::LightTraits BLELight::get_traits() {
    auto traits = light::LightTraits();
    traits.set_supported_color_modes({light::ColorMode::BRIGHTNESS, light::ColorMode::COLOR_TEMPERATURE});
    traits.set_min_mireds(153.0f);
    traits.set_max_mireds(370.0f);
    return traits;
}

void BLELight::write_state(light::LightState *state) {
    // 【关键拦截】如果是从 BLE 广播同步过来的状态更新，直接放行，不发送 BLE 指令
    if (ignore_next_write_) {
        ignore_next_write_ = false;
        ESP_LOGD(TAG, "Ignoring write_state (synced from BLE broadcast)");
        return; 
    }

    if (!gateway_) return;

    auto values = state->remote_values;
    bool target_on = values.is_on();
    float brightness = values.get_brightness();
    float color_temp = values.get_color_temperature();

    std::string target_bright_action = map_brightness(brightness);
    std::string target_temp_action = map_color_temp(color_temp);

    if (target_on == is_currently_on_) {
        if (!target_on || (target_bright_action == last_brightness_action_ && target_temp_action == last_color_temp_action_)) {
            return; 
        }
    }

    uint32_t now = millis();
    if (now - last_send_time_ < 500) return; 

    if (!target_on) {
        gateway_->handle_command(device_id_ + ".off");
    } else {
        if (target_temp_action != last_color_temp_action_ || !is_currently_on_) {
            gateway_->handle_command(device_id_ + "." + target_temp_action);
        }
        if (target_bright_action != last_brightness_action_ || !is_currently_on_) {
            gateway_->handle_command(device_id_ + "." + target_bright_action);
        }
    }

    is_currently_on_ = target_on;
    last_brightness_action_ = target_bright_action;
    last_color_temp_action_ = target_temp_action;
    last_send_time_ = now;
}

// 【新增】从 BLE 广播更新状态
void BLELight::update_from_ble(bool is_on, float brightness, float color_temp_mireds) {
    if (!state_parent_) return;

    // 状态去重：如果和当前状态一样，就不更新，避免 HA 状态条疯狂闪烁
    auto current = state_parent_->current_values;
    if (current.is_on() == is_on && 
        abs(current.get_brightness() - brightness) < 0.01f &&
        abs(current.get_color_temperature() - color_temp_mireds) < 1.0f) {
        return;
    }

    ESP_LOGI(TAG, "Sync from BLE: on=%d, bright=%.2f, temp=%.2f", is_on, brightness, color_temp_mireds);

    // 设置标志位，拦截接下来的 write_state
    ignore_next_write_ = true;
    
    auto call = state_parent_->make_call();
    call.set_state(is_on);
    if (is_on) {
        call.set_brightness(brightness);
        call.set_color_temperature(color_temp_mireds);
    }
    call.perform();
}

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

std::string BLELight::map_color_temp(float mireds) {
    if (mireds < 200.0f) return "color_6500";
    if (mireds < 280.0f) return "color_3500";
    return "color_2700";
}

} // namespace ble_light
} // namespace esphome
