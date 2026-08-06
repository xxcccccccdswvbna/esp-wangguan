#include "ble_gateway.h"
#include "esphome/core/log.h"
#include "esp_gap_ble_api.h"
#include <cctype>

namespace esphome {
namespace ble_gateway {

static const char *TAG = "ble_gateway";

void BLEGateway::setup() {
    ESP_LOGI(TAG, "BLE Gateway setup started");
    config_manager_.load();

    command_router_.set_gateway(this);
    command_router_.set_config(&config_manager_);
    ESP_LOGI(TAG, "BLE Gateway ready");
}

void BLEGateway::loop() {
    const uint32_t now = millis();
    if (cooldown_) {
        if (now - adv_stop_time_ < ADV_COOLDOWN_MS) return;
        cooldown_ = false;
    }
    if (adv_running_ && now - adv_start_time_ >= ADV_DURATION_MS) {
        esp_ble_gap_stop_advertising();
        adv_running_   = false;
        adv_stop_time_ = now;
        cooldown_      = true;
        if (!packet_queue_.empty()) {
            next_packet_time_    = now + PACKET_GAP_MS;
            waiting_next_packet_ = true;
        }
    }
    if (waiting_next_packet_ && now >= next_packet_time_) {
        waiting_next_packet_ = false;
        send_next_packet();
    }
}

std::vector<uint8_t> BLEGateway::hex_to_bytes(const std::string &hex) {
    std::vector<uint8_t> data;
    data.reserve(hex.size() / 2);
    char pair[3] = {0, 0, 0};
    int n = 0;
    for (char c : hex) {
        if (!std::isxdigit(static_cast<unsigned char>(c))) continue;
        pair[n++] = c;
        if (n == 2) {
            data.push_back(static_cast<uint8_t>(strtol(pair, nullptr, 16)));
            n = 0;
        }
    }
    return data;
}

std::vector<std::string> BLEGateway::split_by(const std::string &s, char delim) {
    std::vector<std::string> out;
    size_t start = 0;
    while (true) {
        size_t pos = s.find(delim, start);
        if (pos == std::string::npos) {
            out.push_back(s.substr(start));
            return out;
        }
        out.push_back(s.substr(start, pos - start));
        start = pos + 1;
    }
}

bool BLEGateway::dispatch_action_(const std::string &hex) {
    size_t pos = hex.rfind('.');
    if (pos == std::string::npos) return false;
    std::string device_id   = hex.substr(0, pos);
    std::string action_name = hex.substr(pos + 1);
    const BLEAction *act = config_manager_.find_action(device_id, action_name);
    if (!act) return false;
    enqueue_packets(act->packets);
    return true;
}

void BLEGateway::send_hex(const std::string &hex) {
    if (hex.rfind("020102", 0) != 0 && hex.find('|') == std::string::npos) {
        if (!dispatch_action_(hex)) ESP_LOGW(TAG, "device command not found: %s", hex.c_str());
        return;
    }
    if (hex.find('|') != std::string::npos) {
        enqueue_packets(split_by(hex, '|'));
        return;
    }
    send_raw_packet(hex);
}

void BLEGateway::handle_command(const std::string &cmd) {
    auto p1 = cmd.find('.');
    if (p1 == std::string::npos) return;
    auto p2 = cmd.find('.', p1 + 1);
    if (p2 == std::string::npos) return;
    std::string device = cmd.substr(0, p2);
    std::string action = cmd.substr(p2 + 1);
    send_command(device, action);
}

bool BLEGateway::send_command(const std::string &device, const std::string &action) {
    return command_router_.send_command(device, action);
}

void BLEGateway::enqueue_packets(const std::vector<std::string> &packets) {
    if (packets.empty()) return;
    if (adv_running_ || waiting_next_packet_) {
        packet_queue_.insert(packet_queue_.end(), packets.begin(), packets.end());
    } else {
        packet_queue_.assign(packets.begin(), packets.end());
    }
    if (!adv_running_ && !waiting_next_packet_) {
        send_next_packet();
    }
}

void BLEGateway::send_next_packet() {
    if (packet_queue_.empty()) return;
    std::string packet = std::move(packet_queue_.front());
    packet_queue_.pop_front();
    send_raw_packet(packet);
}

void BLEGateway::send_raw_packet(const std::string &packet) {
    ESP_LOGI(TAG, "BLE TX RAW: %s", packet.c_str());
    auto data = hex_to_bytes(packet);
    if (data.size() < MIN_PACKET_BYTES) return;

    esp_err_t err = esp_ble_gap_config_adv_data_raw(data.data(), data.size());
    esp_ble_adv_params_t params = {};
    params.adv_int_min = ADV_INT_MIN;
    params.adv_int_max = ADV_INT_MAX;
    params.adv_type    = ADV_TYPE_NONCONN_IND;
    params.channel_map = ADV_CHNL_ALL;

    esp_ble_gap_start_advertising(&params);
    adv_start_time_ = millis();
    adv_running_    = true;
}

bool BLEGateway::parse_status(const std::string &hex) { return true; }

// 🔥 新增接口实现
const BLEDevice* BLEGateway::get_device(const std::string &device_id) {
    return config_manager_.find_device(device_id);
}

namespace midea {
    std::vector<uint8_t> create_encode_table(const uint8_t mac[6]) {
        std::vector<uint8_t> table;
        int left = 0, right = 1;
        while (left < 5) {
            table.push_back((mac[left] + mac[right]) & 0xFF);
            right++;
            if (right == 6) { left++; right = left + 1; }
        }
        uint8_t sum = 0;
        for(int i=0; i<6; i++) sum += mac[i];
        table.push_back(sum & 0xFF);
        return table;
    }

    std::vector<uint8_t> build_packet(const uint8_t mac_le[6], uint8_t cmd_type, const std::vector<uint8_t>& values) {
        auto table = create_encode_table(mac_le);
        uint8_t channel = 0x01, version = 0x01;
        std::vector<uint8_t> payload(15, 0);
        payload[0] = channel; payload[1] = version; payload[2] = cmd_type;
        for(size_t i=0; i<values.size() && i<12; i++) payload[3+i] = values[i];
        
        uint8_t checksum = channel + version + cmd_type;
        for(uint8_t v : values) checksum += v;
        payload[14] = checksum;
        
        uint8_t index = 0; 
        uint8_t flag = (0x01 << 4) | (index & 0x0F);
        
        std::vector<uint8_t> packet = {0x02, 0x01, 0x02, 0x1B, 0xFF, 0x11, 0x4D, 0x19, flag};
        for(int i=0; i<6; i++) packet.push_back(mac_le[i]); 
        packet.push_back(channel);
        
        for(int i=0; i<14; i++) {
            packet.push_back(payload[i+1] ^ table[(index + i) % 16]);
        }
        return packet;
    }
}

void BLEGateway::send_midea_command(const std::string &mac_str, uint8_t cmd_type, const std::vector<uint8_t> &values) {
    unsigned int m[6];
    if (sscanf(mac_str.c_str(), "%x:%x:%x:%x:%x:%x", &m[0], &m[1], &m[2], &m[3], &m[4], &m[5]) != 6) {
        ESP_LOGE(TAG, "Invalid MAC: %s", mac_str.c_str());
        return;
    }
    uint8_t mac_le[6];
    for(int i=0; i<6; i++) mac_le[i] = (uint8_t)m[5-i];

    auto cmd_pkt = midea::build_packet(mac_le, cmd_type, values);
    auto end_pkt = midea::build_packet(mac_le, 0, {0x00});

    auto to_hex = [](const std::vector<uint8_t>& data) {
        std::string hex; char buf[3];
        for(uint8_t b : data) { sprintf(buf, "%02X", b); hex += buf; }
        return hex;
    };

    std::string cmd_hex = to_hex(cmd_pkt);
    std::string end_hex = to_hex(end_pkt);

    this->send_raw_packet(cmd_hex);
    this->set_timeout(50, [this, end_hex]() {
        this->send_raw_packet(end_hex);
    });
}

void BLEGateway::send_midea_command_delayed(const std::string &mac_str, uint8_t cmd_type, const std::vector<uint8_t> &values, uint32_t delay_ms) {
    if (delay_ms == 0) {
        send_midea_command(mac_str, cmd_type, values);
    } else {
        this->set_timeout(delay_ms, [this, mac_str, cmd_type, values]() {
            this->send_midea_command(mac_str, cmd_type, values);
        });
    }
}

}  // namespace ble_gateway
}  // namespace esphome
