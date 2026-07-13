#pragma once

#include "esphome/components/light/light_output.h"
#include "esphome/components/light/light_state.h"

#include "ble_gateway.h"


namespace esphome {
namespace ble_gateway {


class BLELight : public Component,
                 public light::LightOutput
{


public:


    void set_gateway(
        BLEGateway *gateway
    )
    {
        gateway_ = gateway;
    }



    void set_device(
        std::string id
    )
    {
        device_id_ = id;
    }




    light::LightTraits get_traits() override;



    void write_state(
        light::LightState *state
    ) override;



protected:

    BLEGateway *gateway_{nullptr};


    std::string device_id_;


};



}
}
