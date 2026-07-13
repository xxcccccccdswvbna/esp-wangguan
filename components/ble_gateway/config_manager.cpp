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




bool ConfigManager::get_action(
    const std::string &command,
    BLEAction &action
)

{


    size_t pos =
        command.rfind(".");


    if(
        pos == std::string::npos
    )
    {
        return false;
    }



    std::string device_id =
        command.substr(
            0,
            pos
        );


    std::string action_name =
        command.substr(
            pos + 1
        );



    for(
        auto &device : devices_
    )
    {

        if(
            device.id == device_id
        )
        {


            auto it =
                device.actions.find(
                    action_name
                );


            if(
                it != device.actions.end()
            )
            {

                action =
                    it->second;


                return true;

            }

        }

    }



    ESP_LOGW(
        TAG,
        "action not found:%s",
        command.c_str()
    );



    return false;

}



}
}
