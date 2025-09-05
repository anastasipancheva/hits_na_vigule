#include "crypto.h"
#include <iostream>
#include <random>
#include <cstring>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/aes.h>
#include <openssl/err.h>

CryptoService::CryptoService() {
    // Инициализация OpenSSL
    OpenSSL_add_all_algorithms();
    ERR_load_crypto_strings();
    
    // Получаем ключ из переменной окружения или генерируем новый
    master_key_ = get_key_from_env();
    if (master_key_.empty()) {
        master_key_ = generate_key();
        std::cout << "Сгенерирован новый мастер-ключ. Сохраните его в переменной окружения MASTER_KEY" << std::endl;
        std::cout << "Ключ (hex): ";
        for (uint8_t byte : master_key_) {
            printf("%02x", byte);
        }
        std::cout << std::endl;
    }
}

CryptoService::~CryptoService() {
    // Очистка памяти ключа
    if (!master_key_.empty()) {
        OPENSSL_cleanse(master_key_.data(), master_key_.size());
    }
    EVP_cleanup();
    ERR_free_strings();
}

std::vector<uint8_t> CryptoService::generate_key() {
    std::vector<uint8_t> key(32); // 256 бит
    if (RAND_bytes(key.data(), key.size()) != 1) {
        std::cerr << "Ошибка генерации ключа" << std::endl;
        return {};
    }
    return key;
}

std::vector<uint8_t> CryptoService::get_key_from_env() {
    const char* env_key = std::getenv("MASTER_KEY");
    if (!env_key) {
        return {};
    }
    
    std::string key_str(env_key);
    if (key_str.length() != 64) { // 32 байта = 64 hex символа
        std::cerr << "Неверная длина ключа в MASTER_KEY (должно быть 64 hex символа)" << std::endl;
        return {};
    }
    
    std::vector<uint8_t> key(32);
    for (size_t i = 0; i < 32; ++i) {
        std::string byte_str = key_str.substr(i * 2, 2);
        key[i] = static_cast<uint8_t>(std::stoul(byte_str, nullptr, 16));
    }
    
    return key;
}

void CryptoService::set_master_key(const std::vector<uint8_t>& key) {
    if (key.size() != 32) {
        throw std::invalid_argument("Ключ должен быть 256 бит (32 байта)");
    }
    master_key_ = key;
}

std::vector<uint8_t> CryptoService::get_master_key() const {
    return master_key_;
}

std::vector<uint8_t> CryptoService::generate_nonce() {
    std::vector<uint8_t> nonce(12); // 96 бит для GCM
    if (RAND_bytes(nonce.data(), nonce.size()) != 1) {
        std::cerr << "Ошибка генерации nonce" << std::endl;
        return {};
    }
    return nonce;
}

std::vector<uint8_t> CryptoService::encrypt(const std::string& plaintext, const std::string& associated_data) {
    if (master_key_.empty()) {
        std::cerr << "Мастер-ключ не установлен" << std::endl;
        return {};
    }
    
    // Генерируем nonce
    std::vector<uint8_t> nonce = generate_nonce();
    if (nonce.empty()) {
        return {};
    }
    
    // Создаем контекст шифрования
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        std::cerr << "Ошибка создания контекста шифрования" << std::endl;
        return {};
    }
    
    // Инициализируем шифрование
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr) != 1) {
        std::cerr << "Ошибка инициализации шифрования" << std::endl;
        EVP_CIPHER_CTX_free(ctx);
        return {};
    }
    
    // Устанавливаем nonce
    if (EVP_EncryptInit_ex(ctx, nullptr, nullptr, master_key_.data(), nonce.data()) != 1) {
        std::cerr << "Ошибка установки nonce" << std::endl;
        EVP_CIPHER_CTX_free(ctx);
        return {};
    }
    
    // Добавляем associated data если есть
    if (!associated_data.empty()) {
        int len;
        if (EVP_EncryptUpdate(ctx, nullptr, &len, 
                             reinterpret_cast<const uint8_t*>(associated_data.data()), 
                             associated_data.length()) != 1) {
            std::cerr << "Ошибка добавления associated data" << std::endl;
            EVP_CIPHER_CTX_free(ctx);
            return {};
        }
    }
    
    // Шифруем данные
    std::vector<uint8_t> ciphertext(plaintext.length() + EVP_CIPHER_block_size(EVP_aes_256_gcm()));
    int len;
    if (EVP_EncryptUpdate(ctx, ciphertext.data(), &len,
                         reinterpret_cast<const uint8_t*>(plaintext.data()),
                         plaintext.length()) != 1) {
        std::cerr << "Ошибка шифрования данных" << std::endl;
        EVP_CIPHER_CTX_free(ctx);
        return {};
    }
    
    int ciphertext_len = len;
    
    // Завершаем шифрование
    if (EVP_EncryptFinal_ex(ctx, ciphertext.data() + len, &len) != 1) {
        std::cerr << "Ошибка завершения шифрования" << std::endl;
        EVP_CIPHER_CTX_free(ctx);
        return {};
    }
    
    ciphertext_len += len;
    
    // Получаем тег аутентификации
    std::vector<uint8_t> tag(16);
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag.data()) != 1) {
        std::cerr << "Ошибка получения тега аутентификации" << std::endl;
        EVP_CIPHER_CTX_free(ctx);
        return {};
    }
    
    EVP_CIPHER_CTX_free(ctx);
    
    // Объединяем nonce + ciphertext + tag
    std::vector<uint8_t> result;
    result.reserve(nonce.size() + ciphertext_len + tag.size());
    result.insert(result.end(), nonce.begin(), nonce.end());
    result.insert(result.end(), ciphertext.begin(), ciphertext.begin() + ciphertext_len);
    result.insert(result.end(), tag.begin(), tag.end());
    
    return result;
}

std::string CryptoService::decrypt(const std::vector<uint8_t>& encrypted_data, const std::string& associated_data) {
    if (master_key_.empty()) {
        std::cerr << "Мастер-ключ не установлен" << std::endl;
        return "";
    }
    
    if (encrypted_data.size() < 28) { // 12 (nonce) + 16 (tag) = минимум
        std::cerr << "Неверный размер зашифрованных данных" << std::endl;
        return "";
    }
    
    // Извлекаем компоненты
    std::vector<uint8_t> nonce(encrypted_data.begin(), encrypted_data.begin() + 12);
    std::vector<uint8_t> tag(encrypted_data.end() - 16, encrypted_data.end());
    std::vector<uint8_t> ciphertext(encrypted_data.begin() + 12, encrypted_data.end() - 16);
    
    // Создаем контекст расшифровки
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        std::cerr << "Ошибка создания контекста расшифровки" << std::endl;
        return "";
    }
    
    // Инициализируем расшифровку
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr) != 1) {
        std::cerr << "Ошибка инициализации расшифровки" << std::endl;
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    // Устанавливаем nonce
    if (EVP_DecryptInit_ex(ctx, nullptr, nullptr, master_key_.data(), nonce.data()) != 1) {
        std::cerr << "Ошибка установки nonce" << std::endl;
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    // Добавляем associated data если есть
    if (!associated_data.empty()) {
        int len;
        if (EVP_DecryptUpdate(ctx, nullptr, &len,
                             reinterpret_cast<const uint8_t*>(associated_data.data()),
                             associated_data.length()) != 1) {
            std::cerr << "Ошибка добавления associated data" << std::endl;
            EVP_CIPHER_CTX_free(ctx);
            return "";
        }
    }
    
    // Расшифровываем данные
    std::vector<uint8_t> plaintext(ciphertext.size() + EVP_CIPHER_block_size(EVP_aes_256_gcm()));
    int len;
    if (EVP_DecryptUpdate(ctx, plaintext.data(), &len, ciphertext.data(), ciphertext.size()) != 1) {
        std::cerr << "Ошибка расшифровки данных" << std::endl;
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    int plaintext_len = len;
    
    // Устанавливаем тег аутентификации
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16, tag.data()) != 1) {
        std::cerr << "Ошибка установки тега аутентификации" << std::endl;
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    // Завершаем расшифровку
    if (EVP_DecryptFinal_ex(ctx, plaintext.data() + len, &len) != 1) {
        std::cerr << "Ошибка завершения расшифровки (возможно, неверный тег)" << std::endl;
        EVP_CIPHER_CTX_free(ctx);
        return "";
    }
    
    plaintext_len += len;
    EVP_CIPHER_CTX_free(ctx);
    
    return std::string(reinterpret_cast<const char*>(plaintext.data()), plaintext_len);
}
