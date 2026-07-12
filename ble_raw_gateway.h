#pragma once


#include "esphome.h"


#include "esp_gap_ble_api.h"
#include "esp_bt_defs.h"
#include "esp_bt_main.h"



static esp_ble_adv_params_t adv_params =
{

    .adv_int_min = 0x20,

    .adv_int_max = 0x40,

    .adv_type = ADV_TYPE_NONCONN_IND,

    .own_addr_type = BLE_ADDR_TYPE_PUBLIC,

    .channel_map = ADV_CHNL_ALL,

    .adv_filter_policy = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY,

};



std::vector<uint8_t> hex_to_bytes(
    const char *hex
)
{

    std::vector<uint8_t> out;


    int len=strlen(hex);


    for(int i=0;i<len;i+=2)
    {

        char buf[3];

        buf[0]=hex[i];

        buf[1]=hex[i+1];

        buf[2]=0;


        out.push_back(
            strtoul(buf,nullptr,16)
        );

    }


    return out;

}



void ble_send_raw_hex(
    const char *hex
)
{

    auto data =
    hex_to_bytes(hex);



    if(data.size()==0)
        return;



    esp_ble_gap_config_adv_data_raw(
        data.data(),
        data.size()
    );


    delay(30);



    esp_ble_gap_start_advertising(
        &adv_params
    );


}
