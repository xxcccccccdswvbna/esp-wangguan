#include "device_table.h"


namespace esphome {
namespace ble_gateway {



void DeviceTable::load(
    std::vector<BLEDevice> &devices
)
{


    /*
     * 添加设备
     */

    add_device(
        devices,
        "light.room1",
        "light",
        "卧室灯"
    );



    /*
     * 灯 开
     */

    add_action(
        devices,
        "light.room1",
        "on",
        {

"0201021BFF114D1914F0CF2D70000001F1FC39CFCF9D2D2D7070005CBF1D68",

"0201021BFF114D1911F0CF2D700000011C60F0F0FC3FCFCF9D2D2D7070005E"

        }
    );



    /*
     * 灯 关
     */

    add_action(
        devices,
        "light.room1",
        "off",
        {

"0201021BFF114D191AF0CF2D700000012C2D7670005CBF1D60F0F0FC3FCFC7",

"0201021BFF114D1912F0CF2D7000000161F0F0FC3FCFCF9D2D2D7070005CBD"

        }
    );



}




void DeviceTable::add_device(
    std::vector<BLEDevice> &devices,
    std::string id,
    std::string type,
    std::string name
)
{


    BLEDevice device;


    device.id = id;


    device.type = type;


    device.name = name;


    devices.push_back(
        device
    );


}





void DeviceTable::add_action(
    std::vector<BLEDevice> &devices,
    std::string device_id,
    std::string action,
    std::vector<std::string> packets
)
{


    for(
        auto &device : devices
    )
    {


        if(
            device.id == device_id
        )
        {


            BLEAction act;


            act.name =
                action;


            act.packets =
                packets;



            device.actions[action]
                =
                act;


            return;


        }


    }


}



}
}