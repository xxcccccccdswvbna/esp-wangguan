#pragma once


#include "esphome.h"


#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_gap_ble_api.h"



extern esphome::mqtt::MQTTClientComponent *mqtt_client;



// =====================
// HEX转换
// =====================

std::vector<uint8_t> hex_to_bytes(const char *hex)
{

    std::vector<uint8_t> data;


    while(*hex)
    {

        char byte[3];

        byte[0]=hex[0];
        byte[1]=hex[1];
        byte[2]=0;


        data.push_back(
            strtol(byte,nullptr,16)
        );


        hex+=2;

    }


    return data;
}



// =====================
// BLE发送
// =====================


static esp_ble_adv_params_t adv_params =
{

    .adv_int_min = 0x20,
    .adv_int_max = 0x40,

    .adv_type = ADV_TYPE_NONCONN_IND,

    .own_addr_type =
    BLE_ADDR_TYPE_PUBLIC,

    .channel_map =
    ADV_CHNL_ALL,

    .adv_filter_policy =
    ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY

};



void ble_send_raw_hex(
    const char *hex
)
{

    auto data =
    hex_to_bytes(hex);


    if(data.empty())
        return;



    esp_ble_gap_config_adv_data_raw(
        data.data(),
        data.size()
    );


    delay(20);


    esp_ble_gap_start_advertising(
        &adv_params
    );

}



// =====================
// BLE扫描回调
// =====================


static void gap_callback(
    esp_gap_ble_cb_event_t event,
    esp_ble_gap_cb_param_t *param
)
{


    if(event ==
       ESP_GAP_BLE_SCAN_RESULT_EVT)
    {


        auto result =
        param->scan_rst;



        if(result.search_evt ==
           ESP_GAP_SEARCH_INQ_RES_EVT)
        {


            std::string raw;



            for(int i=0;
                i<result.adv_data_len;
                i++)
            {

                char buf[3];

                sprintf(
                    buf,
                    "%02X",
                    result.ble_adv[i]
                );


                raw += buf;

            }



            if(raw.length())
            {


                id(mqtt_client).publish(
                    "ct1/ble/receive",
                    raw.c_str()
                );


            }

        }

    }

}




// =====================
// 初始化
// =====================

class BLERawGateway :
public Component
{

public:


void setup() override
{

    esp_bt_controller_mem_release(
        ESP_BT_MODE_CLASSIC_BT
    );


    esp_bt_controller_config_t bt_cfg =
        BT_CONTROLLER_INIT_CONFIG_DEFAULT();


    esp_bt_controller_init(
        &bt_cfg
    );


    esp_bt_controller_enable(
        ESP_BT_MODE_BLE
    );


    esp_bluedroid_init();

    esp_bluedroid_enable();



    esp_ble_gap_register_callback(
        gap_callback
    );



    esp_ble_gap_set_scan_params(
    {
        .scan_type =
        BLE_SCAN_TYPE_ACTIVE,

        .own_addr_type =
        BLE_ADDR_TYPE_PUBLIC,

        .scan_filter_policy =
        BLE_SCAN_FILTER_ALLOW_ALL,

        .scan_interval = 0x50,

        .scan_window = 0x30,

        .scan_duplicate =
        BLE_SCAN_DUPLICATE_DISABLE

    });


}



};
