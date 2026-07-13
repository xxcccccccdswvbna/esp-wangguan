#include "device_table.h"

#include "esphome/core/log.h"



namespace esphome {
namespace ble_gateway {



static const char *TAG="device_table";




void DeviceTable::load(
    std::map<std::string, BLEDeviceCommand> &table
)

{


    ESP_LOGI(
        TAG,
        "Loading device table"
    );



    /*
     * 房间灯
     */

    BLEDeviceCommand light;



    light.name =
        "light.room1.toggle";



    light.packets.push_back(
        "0201021BFFA806810F99CDAB38700000A939387670002078053DCDCDE31BA3"
    );


    light.packets.push_back(
        "0201021BFFA806810F19CDAB38700000043CCDCDE31BABABA8383870700022"
    );



    table[
        light.name
    ] =
        light;



    ESP_LOGI(
        TAG,
        "Device count:%d",
        table.size()
    );

}



}
}
