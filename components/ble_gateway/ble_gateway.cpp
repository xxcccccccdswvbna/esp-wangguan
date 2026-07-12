#include "ble_gateway.h"


#include "esp_gap_ble_api.h"
#include "esp_bt.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG =
"BLE_GATEWAY";



void BLEGateway::setup()
{

  ESP_LOGI(
      TAG,
      "BLE RAW Gateway started"
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
      i+1<hex.length();
      i+=2
  )
  {

    data.push_back(
        strtol(
            hex.substr(i,2).c_str(),
            nullptr,
            16
        )
    );

  }


  return data;

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



  esp_ble_gap_config_adv_data_raw(
      data.data(),
      data.size()
  );


  esp_ble_adv_params_t params{};


  params.adv_int_min =
      0x20;


  params.adv_int_max =
      0x40;


  params.adv_type =
      ADV_TYPE_NONCONN_IND;


  params.channel_map =
      ADV_CHNL_ALL;


  params.adv_filter_policy =
      ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY;



  esp_ble_gap_start_advertising(
      &params
  );


  ESP_LOGI(
      TAG,
      "TX:%s",
      hex.c_str()
  );


}


}
}