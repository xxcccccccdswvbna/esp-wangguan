#include "ble_light.h"

#include "esphome/core/log.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG="ble_light";



light::LightTraits BLELight::get_traits()
{

    auto traits =
        light::LightTraits();


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



    if(
        gateway_ == nullptr
    )
    {

        ESP_LOGE(
            TAG,
            "gateway not set"
        );


        return;

    }



    if(on)
    {

        ESP_LOGI(
            TAG,
            "SEND ON"
        );


        gateway_->send_hex(
            device_id_ + ".on"
        );

    }
    else
    {

        ESP_LOGI(
            TAG,
            "SEND OFF"
        );


        gateway_->send_hex(
            device_id_ + ".off"
        );

    }


}



}
}
