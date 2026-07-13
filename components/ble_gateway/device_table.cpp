#include "device_table.h"


namespace esphome {
namespace ble_gateway {


void DeviceTable::load(
    std::vector<BLEDevice> &devices
)
{

    BLEDevice light;


    light.id =
        "light.room1";


    light.type =
        "light";


    light.name =
        "卧室灯";



    BLEAction on;


    on.name =
        "on";


    on.packets.push_back(
        "0201021BFF114D1914F0CF2D70000001F1FC39CFCF9D2D2D7070005CBF1D68"
    );


    on.packets.push_back(
        "0201021BFF114D1911F0CF2D700000011C60F0F0FC3FCFCF9D2D2D7070005E"
    );


    light.actions["on"] = on;



    devices.push_back(
        light
    );


}


}
}
