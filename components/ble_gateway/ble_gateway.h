#pragma once

#include "esphome/core/component.h"
#include "config_manager.h"
#include "command_router.h"

#include <deque>
#include <string>
#include <vector>

namespace esphome {
namespace ble_gateway {

class BLEGateway : public Component {
public:
    void setup() override;
    void loop() override;

    void send_hex(const std::string &hex);
    void handle_command(const std::string &cmd);
    bool send_command(const std::string &device, const std::string &action);
    bool parse_status(const std::string &hex);
    void enqueue_packets(const std::vector<std::string> &packets);
    
    // 🔥 新增接口
    void send_midea_command(const std::string &mac_str, uint8_t cmd_type, const std::vector<uint8_t> &values);
    void send_midea_command_delayed(const std::string &mac_str, uint8_t cmd_type, const std::vector<uint8_t> &values, uint32_t delay_ms);
    const BLEDevice* get_device(const std::string &device_id);

protected:
    static std::vector<uint8_t> hex_to_bytes(const std::string &hex);
    static std::vector<std::string> split_by(const std::string &s, char delim);

private:
    static constexpr uint32_t ADV_DURATION_MS  = 100;
    static constexpr uint32_t ADV_COOLDOWN_MS  = 800;
    static constexpr uint32_t PACKET_GAP_MS    = 1000;
    static constexpr size_t   MIN_PACKET_BYTES = 5;

    static constexpr uint16_t ADV_INT_MIN = 0x40;
    static constexpr uint16_t ADV_INT_MAX = 0x80;

    ConfigManager config_manager_;
    CommandRouter command_router_;

    bool     adv_running_{false};
    uint32_t adv_start_time_{0};
    uint32_t adv_stop_time_{0};
    bool     cooldown_{false};

    bool     waiting_next_packet_{false};
    uint32_t next_packet_time_{0};
    std::deque<std::string> packet_queue_;

    void send_raw_packet(const std::string &packet);
    void send_next_packet();
    bool dispatch_action_(const std::string &hex);
};

}  // namespace ble_gateway
}  // namespace esphome
