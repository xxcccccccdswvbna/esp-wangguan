#include "ble_gateway.h"

#include "esphome/core/log.h"

#include "esp_gap_ble_api.h"
#include "esp_bt.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG = "ble_gateway";


void BLEGateway::setup()
{

  ESP_LOGI(
      TAG,
      "BLE Gateway start"
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

  ESP_LOGI(
      TAG,
      "send:%s",
      hex.c_str()
  );


}


}
}