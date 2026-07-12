#pragma once


#include "esphome.h"

#include "esp_gap_ble_api.h"
#include "esp_bt.h"
#include "esp_bt_main.h"


namespace esphome {
namespace ble_gateway {


class BLEGateway : public Component {


public:


void setup() override;


void loop() override;



void send_hex(
    const std::string &hex
);



static void gap_callback(
    esp_gap_ble_cb_event_t event,
    esp_ble_gap_cb_param_t *param
);



};


}
}