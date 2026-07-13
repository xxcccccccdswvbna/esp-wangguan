#pragma once


#include "device_model.h"

#include <vector>


namespace esphome {
namespace ble_gateway {


class DeviceTable
{

public:

    static void load(
        std::vector<BLEDevice> &devices
    );


};


}
}
