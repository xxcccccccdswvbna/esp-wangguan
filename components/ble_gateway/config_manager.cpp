#include "config_manager.h"

#include "device_table.h"

#include "esphome/core/log.h"



namespace esphome {
namespace ble_gateway {



static const char *TAG="config_manager";




void ConfigManager::load()
{


    DeviceTable::load(
        commands_
    );


    ESP_LOGI(
        TAG,
        "Config loaded:%d",
        commands_.size()
    );


}




bool ConfigManager::get_decice(
    const std::string &name,
    BLEDeviceCommand &cmd
)

{


    auto it =
        commands_.find(name);



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
