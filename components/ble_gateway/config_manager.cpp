#include "config_manager.h"

#include "esphome/core/log.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG =
    "config_manager";



bool ConfigManager::load()
{

    /*
     * 第一阶段先内置测试
     *
     * 后面替换成 SPIFFS/LittleFS JSON
     */


    BLEDeviceCommand light;


    light.name =
        "light_toggle";


    light.delay =
        800;


    light.packets.push_back(
        "0201021BFFA806810F99CDAB38700000A939387670002078053DCDCDE31BA3"
    );


    light.packets.push_back(
        "0201021BFFA806810F19CDAB38700000043CCDCDE31BABABA8383870700022"
    );



    commands_.push_back(
        light
    );



    ESP_LOGI(
        TAG,
        "commands loaded:%d",
        commands_.size()
    );


    return true;

}





bool ConfigManager::get_command(
    const std::string &name,
    BLEDeviceCommand &cmd
)

{


    for(auto &item : commands_)
    {

        if(item.name == name)
        {

            cmd=item;

            return true;

        }

    }


    ESP_LOGW(
        TAG,
        "command not found:%s",
        name.c_str()
    );


    return false;

}



}
}
