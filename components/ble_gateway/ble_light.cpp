#include "ble_light.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG = "ble_light";



light::LightTraits BLELight::get_traits()
{

    auto traits = light::LightTraits();


    traits.set_supported_color_modes(
        {
            light::ColorMode::BRIGHTNESS,
            light::ColorMode::COLOR_TEMPERATURE
        }
    );


    traits.set_min_mireds(153);
    traits.set_max_mireds(370);


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
