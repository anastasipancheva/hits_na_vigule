#pragma once

#include <string>
#include <vector>
#include <cstdint>

class TOTPGenerator {
public:
    TOTPGenerator(const std::string& secret);
    
    // Генерация и верификация TOTP
    std::string generate_totp(int64_t timestamp = -1);
    bool verify_totp(const std::string& totp_code, int window = 1);
    
    // Утилиты
    static std::string base32_decode(const std::string& encoded);
    static std::string base32_encode(const std::vector<uint8_t>& data);
    static int64_t get_current_timestamp();
    static int64_t get_totp_timestamp(int64_t timestamp = -1);

private:
    std::string secret_;
    std::vector<uint8_t> secret_bytes_;
    
    std::vector<uint8_t> hmac_sha1(const std::vector<uint8_t>& key, const std::vector<uint8_t>& data);
    uint32_t dynamic_truncate(const std::vector<uint8_t>& hmac);
};
