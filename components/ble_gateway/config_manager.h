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






class ConfigManager
{


public:


    void load();



    bool get_command(
        const std::string &name,
        BLEDeviceCommand &cmd
    );



private:


    std::map<
        std::string,
        BLEDeviceCommand
    > commands_;



};




}
}
