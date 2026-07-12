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

}




std::vector<uint8_t>
BLEGateway::hex_to_bytes(
    const std::string &hex
)

{

    std::vector<uint8_t> data;


    for(
        size_t i=0;
        i+1 < hex.length();
        i+=2
    )

    {

        uint8_t b =
            strtol(
                hex.substr(i,2).c_str(),
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
       自动寻找 FF manufacturer 标志

       例如：

       02 01 02
       1B FF
       11 4D ...

       只发送：
       11 4D ...
    */


std::vector<uint8_t> manu;

/*
 * 支持两种输入：
 *
 * 1.
 * 0201021BFFA806......
 *
 * 2.
 * A806......
 */

if (
    data.size() >= 5 &&
    data[0] == 0x02 &&
    data[1] == 0x01
)
{
    size_t start = 0;

    for (size_t i = 0; i < data.size(); i++)
    {
        if (data[i] == 0xFF)
        {
            start = i + 1;
            break;
        }
    }

    if (start == 0)
    {
        ESP_LOGW(TAG, "manufacturer not found");
        return;
    }

    manu.assign(
        data.begin() + start,
        data.end()
    );
}
else
{
    // 已经是 Manufacturer Data

    manu = data;
}

ESP_LOGI(
    TAG,
    "Manufacturer bytes=%d",
    manu.size()
);



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


    params.adv_int_min=0x20;

    params.adv_int_max=0x40;

    params.adv_type=
        ADV_TYPE_NONCONN_IND;

    params.channel_map=
        ADV_CHNL_ALL;



    esp_ble_gap_start_advertising(
        &params
    );



    ESP_LOGI(
        TAG,
        "BLE TX manufacturer length=%d",
        manu.size()
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
