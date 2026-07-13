#pragma once


#include "device_model.h"


namespace esphome {
namespace ble_gateway {


class DeviceTable
{

public:


    static void load(
        std::vector<BLEDevice> &devices
    );


private:


    static void add_device(
        std::vector<BLEDevice> &devices,
        std::string id,
        std::string type,
        std::string name
    );



    static void add_action(
        std::vector<BLEDevice> &devices,
        std::string device_id,
        std::string action,
        std::vector<std::string> packets
    );


};


}
}