#pragma once


#include "esphome/core/component.h"

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



    /*
     * 当前广播状态
     */
    bool adv_running_{false};



    /*
     * 当前广播开始时间
     */
    uint32_t adv_start_time_{0};



    /*
     * 多包队列
     */
    std::vector<std::string> packet_queue_;



    /*
     * 当前等待时间
     */
    uint32_t next_packet_time_{0};



    /*
     * 是否等待下一包
     */
    bool waiting_next_packet_{false};



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
