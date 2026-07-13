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

    // HA实体ID
    std::string id;


    // light / fan
    std::string type;


    // 显示名称
    std::string name;


    // 动作列表
    std::map<std::string, BLEAction> actions;


};



}
}
