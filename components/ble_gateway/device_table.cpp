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
        "0201021BFFA806810F99CDAB38700000A939387670002078053DCDCDE31BA3"
    );


    on.packets.push_back(
        "0201021BFFA806810F19CDAB38700000043CCDCDE31BABABA8383870700022"
    );


    light.actions["on"] = on;



    devices.push_back(
        light
    );


}


}
}
