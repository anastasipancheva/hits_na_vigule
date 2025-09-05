#include "totp.h"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <vector>
#include <openssl/hmac.h>
#include <openssl/sha.h>
#include <chrono>
#include <algorithm>
#include <cctype>

TOTPGenerator::TOTPGenerator(const std::string& secret) : secret_(secret) {
    std::string decoded = base32_decode(secret);
    secret_bytes_ = std::vector<uint8_t>(decoded.begin(), decoded.end());
    if (secret_bytes_.empty()) {
        std::cerr << "Ошибка декодирования base32 секрета" << std::endl;
    }
}

std::string TOTPGenerator::generate_totp(int64_t timestamp) {
    if (secret_bytes_.empty()) {
        return "";
    }
    
    int64_t totp_timestamp = get_totp_timestamp(timestamp);
    
    // Конвертируем timestamp в big-endian байты
    std::vector<uint8_t> time_bytes(8);
    for (int i = 7; i >= 0; --i) {
        time_bytes[i] = static_cast<uint8_t>(totp_timestamp & 0xFF);
        totp_timestamp >>= 8;
    }
    
    // Вычисляем HMAC-SHA1
    std::vector<uint8_t> hmac_result = hmac_sha1(secret_bytes_, time_bytes);
    
    // Динамическое усечение
    uint32_t code = dynamic_truncate(hmac_result);
    
    // Применяем модуль 10^6 для получения 6-значного кода
    code %= 1000000;
    
    // Форматируем как 6-значный код с ведущими нулями
    std::stringstream ss;
    ss << std::setfill('0') << std::setw(6) << code;
    return ss.str();
}

bool TOTPGenerator::verify_totp(const std::string& totp_code, int window) {
    if (totp_code.length() != 6) {
        return false;
    }
    
    // Проверяем, что код содержит только цифры
    if (!std::all_of(totp_code.begin(), totp_code.end(), ::isdigit)) {
        return false;
    }
    
    int64_t current_time = get_totp_timestamp();
    
    // Проверяем код в окне времени
    for (int i = -window; i <= window; ++i) {
        std::string expected_code = generate_totp(current_time + i * 30);
        if (expected_code == totp_code) {
            return true;
        }
    }
    
    return false;
}

std::string TOTPGenerator::base32_decode(const std::string& encoded) {
    const std::string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
    std::string clean_encoded = encoded;
    
    // Удаляем пробелы и приводим к верхнему регистру
    clean_encoded.erase(std::remove_if(clean_encoded.begin(), clean_encoded.end(), ::isspace), clean_encoded.end());
    std::transform(clean_encoded.begin(), clean_encoded.end(), clean_encoded.begin(), ::toupper);
    
    if (clean_encoded.empty()) {
        return "";
    }
    
    // Удаляем padding
    while (!clean_encoded.empty() && clean_encoded.back() == '=') {
        clean_encoded.pop_back();
    }
    
    std::vector<uint8_t> result;
    result.reserve((clean_encoded.length() * 5) / 8);
    
    uint32_t buffer = 0;
    int bits_left = 0;
    
    for (char c : clean_encoded) {
        size_t pos = alphabet.find(c);
        if (pos == std::string::npos) {
            std::cerr << "Неверный символ в base32: " << c << std::endl;
            return "";
        }
        
        buffer = (buffer << 5) | pos;
        bits_left += 5;
        
        if (bits_left >= 8) {
            result.push_back(static_cast<uint8_t>((buffer >> (bits_left - 8)) & 0xFF));
            bits_left -= 8;
        }
    }
    
    return std::string(result.begin(), result.end());
}

std::string TOTPGenerator::base32_encode(const std::vector<uint8_t>& data) {
    const std::string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
    std::string result;
    
    if (data.empty()) {
        return "";
    }
    
    uint32_t buffer = 0;
    int bits_left = 0;
    
    for (uint8_t byte : data) {
        buffer = (buffer << 8) | byte;
        bits_left += 8;
        
        while (bits_left >= 5) {
            result += alphabet[(buffer >> (bits_left - 5)) & 0x1F];
            bits_left -= 5;
        }
    }
    
    if (bits_left > 0) {
        result += alphabet[(buffer << (5 - bits_left)) & 0x1F];
    }
    
    // Добавляем padding
    while (result.length() % 8 != 0) {
        result += '=';
    }
    
    return result;
}

int64_t TOTPGenerator::get_current_timestamp() {
    return std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
}

int64_t TOTPGenerator::get_totp_timestamp(int64_t timestamp) {
    if (timestamp == -1) {
        timestamp = get_current_timestamp();
    }
    return timestamp / 30; // TOTP использует 30-секундные интервалы
}

std::vector<uint8_t> TOTPGenerator::hmac_sha1(const std::vector<uint8_t>& key, const std::vector<uint8_t>& data) {
    std::vector<uint8_t> result(SHA_DIGEST_LENGTH);
    unsigned int len;
    
    if (HMAC(EVP_sha1(), key.data(), key.size(), data.data(), data.size(), 
             result.data(), &len) == nullptr) {
        std::cerr << "Ошибка вычисления HMAC-SHA1" << std::endl;
        return {};
    }
    
    return result;
}

uint32_t TOTPGenerator::dynamic_truncate(const std::vector<uint8_t>& hmac) {
    if (hmac.size() < 20) {
        return 0;
    }
    
    // Берем последний байт как offset
    int offset = hmac[19] & 0x0F;
    
    // Извлекаем 4 байта начиная с offset
    uint32_t code = ((hmac[offset] & 0x7F) << 24) |
                    ((hmac[offset + 1] & 0xFF) << 16) |
                    ((hmac[offset + 2] & 0xFF) << 8) |
                    (hmac[offset + 3] & 0xFF);
    
    return code;
}
