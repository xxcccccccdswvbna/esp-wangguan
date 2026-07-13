#include "config_manager.h"
#include "device_table.h"


namespace esphome {
namespace ble_gateway {


void ConfigManager::load()
{

    DeviceTable table;


    table.load(
        devices_
    );

}



bool ConfigManager::get_action(
    const std::string &device_id,
    const std::string &action,
    BLEAction &result
)
{

    for(
        auto &device :
        devices_
    )
    {


        if(
            device.id == device_id
        )
        {

            auto it =
            device.actions.find(
                action
            );


            if(
                it != device.actions.end()
            )
            {

                result =
                it->second;

                return true;

            }

        }

    }


    return false;

}



}
}
