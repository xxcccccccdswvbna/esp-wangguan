#pragma once


#include "device_model.h"

#include <vector>
#include <string>



namespace esphome {
namespace ble_gateway {


class ConfigManager
{


public:


    void load();



    bool get_action(
        const std::string &device_id,
        const std::string &action,
        BLEAction &result
    );



private:


    std::vector<BLEDevice> devices_;


};


}
}
