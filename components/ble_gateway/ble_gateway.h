#pragma once

#include "esphome/core/component.h"
#include "config_manager.h"
#include "command_router.h"

#include <vector>
#include <string>

namespace esphome {
namespace ble_gateway {

class BLEGateway : public Component {
public:
    void setup() override;
    void loop() override;

    /*
     * MQTT入口
     * 支持: 单包 HEX, 多包 HEX|HEX
     */
    void send_hex(std::string hex);

    /*
     * 新增：处理命令入口 (如 light.room1.on)
     */
    void handle_command(std::string cmd);

    bool send_command(std::string device, std::string action);
    bool parse_status(std::string hex);

protected:
    std::vector<uint8_t> hex_to_bytes(const std::string &hex);

private:
    ConfigManager config_manager_;
    CommandRouter command_router_;

    bool adv_running_{false};
    uint32_t adv_start_time_{0};
    uint32_t adv_stop_time_{0};
    bool cooldown_{false};

    bool waiting_next_packet_{false};
    uint32_t next_packet_time_{0};
    std::vector<std::string> packet_queue_;

    void send_raw_packet(std::string packet);
    void send_next_packet();
};

} // namespace ble_gateway
} // namespace esphome
