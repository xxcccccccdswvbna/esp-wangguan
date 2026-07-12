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
     * MQTT调用
     *
     * 输入完整BLE RAW包
     *
     * 例如：
     * 0201021BFFA806......
     */
    void send_hex(
        std::string hex
    );



    /*
     * 状态解析预留
     */
    bool parse_status(
        std::string hex
    );



 protected:


    /*
     * HEX转换BYTE
     */
    std::vector<uint8_t>
    hex_to_bytes(
        const std::string &hex
    );



 private:


    /*
     * 广播开始时间
     */
    uint32_t adv_start_time_{0};



    /*
     * 当前是否正在广播
     */
    bool adv_running_{false};



};



}
}
