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
        "devices loaded:%d",
        devices_.size()
    );

}




bool ConfigManager::get_command(
    const std::string &id,
    BLEAction &action
)
{


    for(
        auto &device : devices_
    )
    {


        for(
            auto &item : device.actions
        )
        {


            std::string key =
                device.id + "." + item.first;



            if(
                key == id
            )
            {

                action =
                    item.second;


                return true;

            }

        }

    }



    ESP_LOGW(
        TAG,
        "command not found:%s",
        id.c_str()
    );


    return false;

}



}
}
