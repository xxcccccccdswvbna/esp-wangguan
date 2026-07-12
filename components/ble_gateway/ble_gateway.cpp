#include "ble_gateway.h"

#include "esphome/core/log.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG = "ble_gateway";



void BLEGateway::setup()
{

  ESP_LOGI(
    TAG,
    "BLE Gateway component loaded"
  );


}



void BLEGateway::loop()
{


}



}
}