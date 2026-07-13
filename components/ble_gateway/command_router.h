#pragma once

#include <string>

#include "config_manager.h"


namespace esphome {
namespace ble_gateway {


class BLEGateway;


class CommandRouter
{

public:

    void set_gateway(
        BLEGateway *gateway
    );

    void set_config(
        ConfigManager *config
    );


    bool send_command(
        std::string device,
        std::string action
    );


private:

    BLEGateway *gateway_{nullptr};

    ConfigManager *config_{nullptr};

};


}
}
