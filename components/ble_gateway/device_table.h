#pragma once


#include "device_model.h"

#include <vector>
#include <string>


namespace esphome {
namespace ble_gateway {


class DeviceTable
{

public:


    void load(
        std::vector<BLEDevice> &devices
    );



private:


    void add_device(
        std::vector<BLEDevice> &devices,
        std::string id,
        std::string type,
        std::string name
    );



    void add_action(
        std::vector<BLEDevice> &devices,
        std::string device_id,
        std::string action,
        std::vector<std::string> packets
    );


};



}
}
