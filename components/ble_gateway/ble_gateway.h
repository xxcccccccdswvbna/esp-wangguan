#pragma once


#include "esphome.h"

#include <vector>
#include <string>


namespace esphome {
namespace ble_gateway {



class BLEGateway : public Component {


public:


    void setup() override;


    void loop() override;


    void send_hex(std::string hex);



private:


    void start_scan();


    std::vector<uint8_t> hex_to_bytes(
        const std::string &hex
    );


};



}
}