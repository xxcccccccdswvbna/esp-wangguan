#pragma once


#include "esphome/core/component.h"

#include "config_manager.h"

#include <vector>
#include <string>>


namespace esphome {
namespace ble_gateway {


class BLEGateway : public Component {


 public:


    void setup() override;


    void loop() override;



    /*
     * MQTT入口
     *
     * 支持：
     *
     * 单包:
     * HEX
     *
     * 多包:
     * HEX|HEX|HEX
     */
    void send_hex(
        std::string hex
    );



    bool parse_status(
        std::string hex
    );



 protected:


    std::vector<uint8_t>
    hex_to_bytes(
        const std::string &hex
    );



private:

    ConfigManager config_manager_;

    bool adv_running_{false};

    uint32_t adv_start_time_{0};

    bool waiting_next_packet_{false};

    uint32_t next_packet_time_{0};

    bool just_stopped_{false};

    std::vector<std::string> packet_queue_;


    /*
     * 发送单个RAW包
     */
    void send_raw_packet(
        std::string packet
    );



    /*
     * 发送队列下一包
     */
    void send_next_packet();



};



}
}
