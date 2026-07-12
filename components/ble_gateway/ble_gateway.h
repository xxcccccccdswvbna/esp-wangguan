#pragma once


#include "esphome/core/component.h"


namespace esphome {
namespace ble_gateway {


class BLEGateway : public Component {


 public:

  void setup() override;

  void loop() override;


};


}
}