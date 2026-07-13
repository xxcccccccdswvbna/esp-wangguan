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
     *
     * 支持:
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


    bool send_command(
        std::string device,
        std::string action
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
     * 设备配置管理
     */
    ConfigManager config_manager_;


    /*
     * 命令路由
     */
    CommandRouter command_router_;



    /*
     * 当前广播状态
     */
    bool adv_running_{false};


    uint32_t adv_start_time_{0};



    /*
     * 广播停止时间
     */
    uint32_t adv_stop_time_{0};



    /*
     * BLE GAP冷却
     */
    bool cooldown_{false};




    /*
     * 多包发送控制
     */
    bool waiting_next_packet_{false};


    uint32_t next_packet_time_{0};



    std::vector<std::string>
    packet_queue_;




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
