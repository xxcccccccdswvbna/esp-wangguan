#include "config_manager.h"

#include "device_table.h"

#include "esphome/core/log.h"



namespace esphome {
namespace ble_gateway {



static const char *TAG =
    "config_manager";




void ConfigManager::load()
{

    devices_.clear();



    DeviceTable::load(
        devices_
    );



    ESP_LOGI(
        TAG,
        "Config loaded:%d",
        devices_.size()
    );

}




bool ConfigManager::get_command(
    const std::string &name,
    BLEDevice &device
)

{


    for(
        auto &dev : devices_
    )
    {


        if(
            dev.id == name
        )
        {

            device = dev;


            return true;

        }


    }



    ESP_LOGW(
        TAG,
        "device not found:%s",
        name.c_str()
    );



    return false;

}



}
}
