#pragma once

#include <string>

#include "config_manager.h"
#include "ble_gateway.h"


namespace esphome {
namespace ble_gateway {


class CommandRouter {


public:

    void set_gateway(
        BLEGateway *gateway
    )
    {
        gateway_ = gateway;
    }


    void set_config(
        ConfigManager *config
    )
    {
        config_ = config;
    }


    bool send_command(
        std::string device,
        std::string action
    );


protected:

    BLEGateway *gateway_{nullptr};

    ConfigManager *config_{nullptr};


};


}
}
