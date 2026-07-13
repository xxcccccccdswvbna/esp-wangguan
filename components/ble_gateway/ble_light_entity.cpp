#include "ble_light_entity.h"

#include "esphome/core/log.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG =
"ble_light_entity";



light::LightTraits
BLELightEntity::get_traits()
{

    light::LightTraits traits;


    /*
     * 第一版只支持开关
     */

    traits.set_supported_color_modes(
        {
            light::ColorMode::ON_OFF
        }
    );


    return traits;

}



void BLELightEntity::write_state(
    light::LightState *state
)
{

    bool on;


    state->current_values_as_binary(
        &on
    );



    if(!gateway_)
    {
        ESP_LOGE(
            TAG,
            "gateway missing"
        );

        return;
    }



    if(on)
    {

        ESP_LOGI(
            TAG,
            "LIGHT ON"
        );


        gateway_->send_command(
            device_id_,
            "on"
        );

    }
    else
    {

        ESP_LOGI(
            TAG,
            "LIGHT OFF"
        );


        gateway_->send_command(
            device_id_,
            "off"
        );

    }


}



}
}
