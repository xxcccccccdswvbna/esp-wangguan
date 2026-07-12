#include "ble_gateway.h"

#include "esphome/core/log.h"

#include "esp_gap_ble_api.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG = "ble_gateway";



void BLEGateway::setup()
{

    ESP_LOGI(
        TAG,
        "BLE Gateway ready"
    );

}



void BLEGateway::loop()
{

    /*
     * 广播发送完成后自动停止
     */

    if(
        adv_running_ &&
        millis() - adv_start_time_ > 50
    )
    {

        esp_ble_gap_stop_advertising();


        adv_running_ = false;


        ESP_LOGI(
            TAG,
            "BLE ADV STOP"
        );

    }

}




std::vector<uint8_t>
BLEGateway::hex_to_bytes(
    const std::string &hex
)

{

    std::vector<uint8_t> data;


    std::string clean = hex;


    if(
        clean.rfind("0x",0)==0 ||
        clean.rfind("0X",0)==0
    )
    {
        clean =
            clean.substr(2);
    }



    for(
        size_t i=0;
        i+1 < clean.length();
        i+=2
    )

    {

        uint8_t b =
            strtol(
                clean.substr(i,2)
                .c_str(),
                nullptr,
                16
            );


        data.push_back(b);

    }


    return data;

}





void BLEGateway::send_hex(
    std::string hex
)

{

    ESP_LOGI(
        TAG,
        "BLE TX RAW:%s",
        hex.c_str()
    );



    auto data =
        hex_to_bytes(hex);



    if(data.size()<5)
    {

        ESP_LOGW(
            TAG,
            "packet too short"
        );

        return;

    }



    /*
     * 这里直接发送完整RAW广播包
     *
     * 例如：
     *
     * 0201021BFFA806......
     *
     */


    esp_err_t err =
        esp_ble_gap_config_adv_data_raw(
            data.data(),
            data.size()
        );


    ESP_LOGI(
        TAG,
        "RAW ADV len=%d err=%d",
        data.size(),
        err
    );



    esp_ble_adv_params_t params={};


    params.adv_int_min =
        0x20;


    params.adv_int_max =
        0x40;


    params.adv_type =
        ADV_TYPE_NONCONN_IND;


    params.channel_map =
        ADV_CHNL_ALL;



    esp_ble_gap_start_advertising(
        &params
    );



    adv_start_time_ =
        millis();


    adv_running_ =
        true;



    ESP_LOGI(
        TAG,
        "BLE ADV START"
    );

}





bool BLEGateway::parse_status(
    std::string hex
)

{

    ESP_LOGI(
        TAG,
        "BLE RX:%s",
        hex.c_str()
    );


    return true;

}



}
}
