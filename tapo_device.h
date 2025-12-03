#pragma once

#include "tapo_protocol.h"

#define TAPO_MAX_SEND_RETRIES      3
#define TAPO_MAX_RECONNECT_RETRIES 3

class TapoDevice {
private:
    TapoProtocol protocol;

    bool check_state(const String &expected_state) {
        String response = protocol.send_message("{\"method\":\"get_device_info\",\"params\":{}}");
        return response.indexOf(expected_state) != -1;
    }

    bool send_command(const String &command, const String &expected_state = "") {
        for (int i = 0; i < TAPO_MAX_RECONNECT_RETRIES; i++) {
            for (int j = 0; j < TAPO_MAX_SEND_RETRIES; j++) {
                protocol.send_message(command);
                if (expected_state == "" || check_state(expected_state)) {
                    return true;
                }
            }
            Serial.println("TAPO_DEVICE: Failed to send command, rehandshaking...");
            protocol.rehandshake();
        }
        Serial.println("TAPO_DEVICE: Failed to rehandshake, giving up command");
        return false;
    }

    /* helpers */
    String wrap_param(const String &key, const String &value, bool numeric = false) {
        return "\"" + key + "\":" + (numeric ? value : "\"" + value + "\"");
    }

public:
    void begin(const String &ip_address, const String &username, const String &password) {
        protocol.handshake(ip_address, username, password);
    }

    void on() {
        const String command = "{\"method\":\"set_device_info\",\"params\":{\"device_on\":true}}";
        const String expected = "\"device_on\":true";
        send_command(command, expected);
    }

    void off() {
        const String command = "{\"method\":\"set_device_info\",\"params\":{\"device_on\":false}}";
        const String expected = "\"device_on\":false";
        send_command(command, expected);
    }

    String get_status() {
        // Get full device information/status
        return protocol.send_message("{\"method\":\"get_device_info\",\"params\":{}}");
    }

    bool is_on() {
        // Check if device is currently on
        String response = protocol.send_message("{\"method\":\"get_device_info\",\"params\":{}}");
        return response.indexOf("\"device_on\":true") != -1;
    }
};
