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


    bool get_command(
        const std::string &id,
        BLEAction &action
    );


private:

    std::vector<BLEDevice> devices_;


};


}
}
