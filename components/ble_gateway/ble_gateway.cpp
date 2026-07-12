#include "ble_gateway.h"

#include "esphome/core/log.h"

#include "esp_gap_ble_api.h"
#include "esp_bt.h"
#include "esp_bt_main.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG = "ble_gateway";


BLEGateway *global_ble_gateway = nullptr;


void BLEGateway::setup()
{

  ESP_LOGI(TAG, "BLE Gateway start");


  global_ble_gateway = this;


  // 初始化 BLE Controller
  esp_bt_controller_config_t bt_cfg =
      BT_CONTROLLER_INIT_CONFIG_DEFAULT();


  esp_err_t ret;


  ret = esp_bt_controller_init(&bt_cfg);

  if(ret != ESP_OK &&
     ret != ESP_ERR_INVALID_STATE)
  {

    ESP_LOGE(
        TAG,
        "BT controller init failed"
    );

    return;

  }


  ret = esp_bt_controller_enable(
      ESP_BT_MODE_BLE
  );


  if(ret != ESP_OK &&
     ret != ESP_ERR_INVALID_STATE)
  {

    ESP_LOGE(
        TAG,
        "BT enable failed"
    );

    return;

  }


  esp_bluedroid_init();

  esp_bluedroid_enable();


  ESP_LOGI(
      TAG,
      "BLE ready"
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
      size_t i = 0;
      i + 1 < hex.length();
      i += 2
  )

  {

    uint8_t value =
        strtol(
            hex.substr(i,2).c_str(),
            nullptr,
            16
        );


    data.push_back(value);

  }


  return data;

}





void BLEGateway::send_hex(
    std::string hex
)

{


  ESP_LOGI(
      TAG,
      "BLE TX HEX:%s",
      hex.c_str()
  );



  std::vector<uint8_t> data =
      hex_to_bytes(hex);



  if(data.size()==0)
  {

    ESP_LOGW(
        TAG,
        "empty packet"
    );

    return;

  }



  /*
    BLE 广播数据格式

    前面自动加：
    Flags

    后面放：
    Manufacturer data

  */


  esp_ble_adv_data_t adv_data = {};



  adv_data.set_scan_rsp = false;

  adv_data.include_name = false;

  adv_data.include_txpower = false;


  adv_data.manufacturer_len =
      data.size();



  adv_data.p_manufacturer_data =
      data.data();



  esp_ble_gap_config_adv_data(
      &adv_data
  );



  esp_ble_adv_params_t adv_params = {};



  adv_params.adv_int_min =
      0x20;


  adv_params.adv_int_max =
      0x40;


  adv_params.adv_type =
      ADV_TYPE_NONCONN_IND;


  adv_params.own_addr_type =
      BLE_ADDR_TYPE_PUBLIC;


  adv_params.channel_map =
      ADV_CHNL_ALL;



  esp_ble_gap_start_advertising(
      &adv_params
  );



  ESP_LOGI(
      TAG,
      "BLE advertising started len=%d",
      data.size()
  );



}



}
}