#include "ble_gateway.h"


#include "esp_gap_ble_api.h"
#include "esp_bt.h"
#include "esp_bt_main.h"



namespace esphome {
namespace ble_gateway {



static const char *TAG =
"ble_gateway";



BLEGateway *global_gateway;



void BLEGateway::setup()
{


    global_gateway=this;


    ESP_LOGI(
        TAG,
        "BLE RAW Gateway start"
    );


    esp_bt_controller_mem_release(
        ESP_BT_MODE_CLASSIC_BT
    );


}



void BLEGateway::loop()
{


}



std::vector<uint8_t>
BLEGateway::hex_to_bytes(
const std::string &hex
)
{

    std::vector<uint8_t> out;


    for(
        size_t i=0;
        i+1<hex.length();
        i+=2
    )
    {


        uint8_t b =
        strtol(
            hex.substr(i,2).c_str(),
            nullptr,
            16
        );


        out.push_back(b);

    }


    return out;

}



void BLEGateway::send_hex(
std::string hex
)
{


    auto data =
    hex_to_bytes(hex);



    if(data.empty())
    {

        ESP_LOGW(
            TAG,
            "empty packet"
        );

        return;

    }



    esp_ble_adv_data_t adv_data{};


    adv_data.set_scan_rsp=false;


    adv_data.include_name=false;


    adv_data.include_txpower=false;


    esp_ble_gap_config_adv_data_raw(
        data.data(),
        data.size()
    );



    esp_ble_adv_params_t adv_params{};


    adv_params.adv_int_min=0x20;

    adv_params.adv_int_max=0x40;


    adv_params.adv_type=
        ADV_TYPE_NONCONN_IND;


    adv_params.channel_map=
        ADV_CHNL_ALL;


    adv_params.adv_filter_policy=
        ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY;



    esp_ble_gap_start_advertising(
        &adv_params
    );


    ESP_LOGI(
        TAG,
        "BLE TX %s",
        hex.c_str()
    );


}



}
}