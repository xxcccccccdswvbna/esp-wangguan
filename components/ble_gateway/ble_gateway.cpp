#pragma once


#include "esphome/core/component.h"

#include <string>
#include <vector>


namespace esphome {
namespace ble_gateway {



class BLEGateway : public Component {


 public:


  void setup() override;


  void loop() override;


  void send_hex(
      std::string hex
  );



 private:


  std::vector<uint8_t> hex_to_bytes(
      const std::string &hex
  );



};



}
}