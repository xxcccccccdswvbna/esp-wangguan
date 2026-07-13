#include "command_router.h"
#include "ble_gateway.h"


namespace esphome {
namespace ble_gateway {


void CommandRouter::set_gateway(
    BLEGateway *gateway
)
{
    gateway_ = gateway;
}



void CommandRouter::set_config(
    ConfigManager *config
)
{
    config_ = config;
}



bool CommandRouter::send_command(
    std::string device,
    std::string action
)
{

    if(
        !gateway_ ||
        !config_
    )
    {
        return false;
    }


    BLEAction result;


    if(
        !config_->get_action(
            device,
            action,
            result
        )
    )
    {
        return false;
    }


    for(
        auto &packet :
        result.packets
    )
    {

        gateway_->send_hex(
            packet
        );

    }


    return true;

}


}
}
