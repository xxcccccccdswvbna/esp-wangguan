#include "config_manager.h"

#include "esphome/core/log.h"


namespace esphome {
namespace ble_gateway {



static const char *TAG = "config_manager";





void ConfigManager::load()
{


    ESP_LOGI(
        TAG,
        "Loading device commands"
    );



    /*
     * 灯开关
     *
     * 后续所有设备
     * 都在这里注册
     */


    BLEDeviceCommand light_toggle;



    light_toggle.name =
        "light_toggle";



    light_toggle.packets.push_back(
        "0201021BFFA806810F99CDAB38700000A939387670002078053DCDCDE31BA3"
    );


    light_toggle.packets.push_back(
        "0201021BFFA806810F19CDAB38700000043CCDCDE31BABABA8383870700022"
    );



    commands_[
        light_toggle.name
    ] =
        light_toggle;





    ESP_LOGI(
        TAG,
        "Loaded commands: %d",
        commands_.size()
    );


}








bool ConfigManager::get_command(
    const std::string &name,
    BLEDeviceCommand &cmd
)

{


    auto it =
        commands_.find(
            name
        );



    if(
        it == commands_.end()
    )
    {


        ESP_LOGW(
            TAG,
            "command not found:%s",
            name.c_str()
        );


        return false;

    }



    cmd =
        it->second;



    return true;


}






}
}
