#pragma once

#include <string>
#include <vector>
#include <map>


namespace esphome {
namespace ble_gateway {



struct BLEDeviceCommand
{

    std::string name;


    std::vector<std::string> packets;

};




class DeviceTable
{


public:


    static void load(
        std::map<std::string, BLEDeviceCommand> &table
    );



};



}
}
