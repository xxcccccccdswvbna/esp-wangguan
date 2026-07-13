#pragma once


#include "device_table.h"


#include <map>
#include <string>



namespace esphome {
namespace ble_gateway {



class ConfigManager
{


public:


    void load();



    bool get_command(
        const std::string &name,
        BLEDeviceCommand &cmd
    );



private:


    std::map<std::string, BLEDeviceCommand> commands_;



};



}
}
