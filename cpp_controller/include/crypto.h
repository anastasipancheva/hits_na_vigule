#pragma once

#include <string>
#include <vector>
#include <memory>

class CryptoService {
public:
    CryptoService();
    ~CryptoService();

    // Шифрование/дешифрование
    std::vector<uint8_t> encrypt(const std::string& plaintext, const std::string& associated_data = "");
    std::string decrypt(const std::vector<uint8_t>& encrypted_data, const std::string& associated_data = "");

    // Утилиты
    std::vector<uint8_t> generate_key();
    void set_master_key(const std::vector<uint8_t>& key);
    std::vector<uint8_t> get_master_key() const;

private:
    std::vector<uint8_t> master_key_;
    std::vector<uint8_t> generate_nonce();
    std::vector<uint8_t> get_key_from_env();
};
