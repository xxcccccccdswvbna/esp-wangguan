#include "ble_gateway.h"


namespace esphome {
namespace ble_gateway {


static BLEGateway *instance;



static esp_ble_adv_params_t adv_params =
{

    .adv_int_min = 0x20,
    .adv_int_max = 0x40,

    .adv_type =
        ADV_TYPE_NONCONN_IND,

    .own_addr_type =
        BLE_ADDR_TYPE_PUBLIC,

    .channel_map =
        ADV_CHNL_ALL,

    .adv_filter_policy =
        ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY

};



std::vector<uint8_t>
hex_decode(const std::string &hex)
{

    std::vector<uint8_t> out;


    for(size_t i=0;i<hex.length();i+=2)
    {

        std::string b =
            hex.substr(i,2);


        out.push_back(
            strtol(
                b.c_str(),
                nullptr,
                16
            )
        );

    }


    return out;
}




void BLEGateway::setup()
{

    instance=this;


    esp_bt_controller_mem_release(
        ESP_BT_MODE_CLASSIC_BT
    );


    esp_bt_controller_config_t cfg =
        BT_CONTROLLER_INIT_CONFIG_DEFAULT();


    esp_bt_controller_init(
        &cfg
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


    esp_ble_gap_start_scanning(
        0
    );


}




void BLEGateway::send_hex(
    const std::string &hex
)
{


    auto data =
        hex_decode(hex);


    if(data.empty())
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




void BLEGateway::loop()
{

}





void BLEGateway::gap_callback(
    esp_gap_ble_cb_event_t event,
    esp_ble_gap_cb_param_t *param
)
{


    if(event ==
       ESP_GAP_BLE_SCAN_RESULT_EVT)
    {


        auto r =
            param->scan_rst;



        if(r.search_evt ==
           ESP_GAP_SEARCH_INQ_RES_EVT)
        {


            std::string raw;


            for(int i=0;
                i<r.adv_data_len;
                i++)
            {

                char buf[3];


                sprintf(
                    buf,
                    "%02X",
                    r.ble_adv[i]
                );


                raw += buf;

            }


            ESP_LOGI(
                "BLE_RAW",
                "%s",
                raw.c_str()
            );


        }


    }


}


}
}