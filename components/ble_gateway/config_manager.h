#pragma once

#include <string>
#include <vector>


namespace esphome {
namespace ble_gateway {


struct BLEDeviceCommand
{
    std::string name;

    std::vector<std::string> packets;

    uint32_t delay;
};



class ConfigManager
{

public:

    bool load();


    bool get_command(
        const std::string &name,
        BLEDeviceCommand &cmd
    );


private:

    std::vector<BLEDeviceCommand> commands_;


};



}
}
