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


}
}
