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




bool ConfigManager::get_action(
    const std::string &device_id,
    const std::string &action,
    BLEAction &result
)

{


    for(auto &device : devices_)
    {


        if(device.id != device_id)
            continue;



        auto it =
            device.actions.find(action);



        if(
            it ==
            device.actions.end()
        )
        {

            ESP_LOGW(
                TAG,
                "action not found:%s",
                action.c_str()
            );


            return false;

        }


        result =
            it->second;


        return true;

    }



    ESP_LOGW(
        TAG,
        "device not found:%s",
        device_id.c_str()
    );


    return false;

}



}
}
