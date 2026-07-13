#pragma once

#include <string>
#include <vector>
#include <map>


namespace esphome {
namespace ble_gateway {


struct BLEAction
{

    std::string name;


    std::vector<std::string> packets;

};



struct BLEDevice
{

    std::string id;


    std::string type;


    std::string name;


    std::map<std::string, BLEAction> actions;

};



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