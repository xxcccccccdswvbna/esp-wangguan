#include "ble_light.h"

#include "esphome/core/log.h"


namespace esphome {
namespace ble_gateway {



static const char *TAG="ble_light";



light::LightTraits BLELight::get_traits()
{

    auto traits =
        light::LightTraits();



    // 支持亮度

    traits.set_supported_color_modes(
        {
            light::ColorMode::BRIGHTNESS
        }
    );


    return traits;

}




void BLELight::write_state(
    light::LightState *state
)
{


    bool on;


    state->current_values_as_binary(
        &on
    );



    if(on)
    {

        ESP_LOGI(
            TAG,
            "LIGHT ON"
        );


        gateway_->send_hex(
            device_id_ + ".on"
        );


    }
    else
    {

        ESP_LOGI(
            TAG,
            "LIGHT OFF"
        );


        gateway_->send_hex(
            device_id_ + ".off"
        );

    }



}



}
}
