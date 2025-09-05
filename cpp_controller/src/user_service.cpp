#include "user_service.h"
#include <iostream>

UserService::UserService() {
    database_ = std::make_unique<Database>();
    crypto_service_ = std::make_unique<CryptoService>();
}

UserService::~UserService() = default;

bool UserService::create_user(const std::string& username) {
    if (username.empty()) {
        std::cerr << "Имя пользователя не может быть пустым" << std::endl;
        return false;
    }
    
    if (user_exists(username)) {
        std::cerr << "Пользователь '" << username << "' уже существует" << std::endl;
        return false;
    }
    
    return database_->create_user(username);
}

bool UserService::save_user_secret(const std::string& username, const std::string& secret_plain) {
    if (username.empty() || secret_plain.empty()) {
        std::cerr << "Имя пользователя и секрет не могут быть пустыми" << std::endl;
        return false;
    }
    
    if (!user_exists(username)) {
        std::cerr << "Пользователь '" << username << "' не найден" << std::endl;
        return false;
    }
    
    try {
        // Шифруем секрет с использованием имени пользователя как associated data
        std::vector<uint8_t> encrypted_secret = crypto_service_->encrypt(secret_plain, username);
        if (encrypted_secret.empty()) {
            std::cerr << "Ошибка шифрования секрета" << std::endl;
            return false;
        }
        
        return database_->update_user_secret(username, encrypted_secret);
    } catch (const std::exception& e) {
        std::cerr << "Ошибка при сохранении секрета: " << e.what() << std::endl;
        return false;
    }
}

bool UserService::revoke_user_access(const std::string& username) {
    if (username.empty()) {
        std::cerr << "Имя пользователя не может быть пустым" << std::endl;
        return false;
    }
    
    if (!user_exists(username)) {
        std::cerr << "Пользователь '" << username << "' не найден" << std::endl;
        return false;
    }
    
    return database_->revoke_user_access(username);
}

bool UserService::delete_user(const std::string& username) {
    if (username.empty()) {
        std::cerr << "Имя пользователя не может быть пустым" << std::endl;
        return false;
    }
    
    if (!user_exists(username)) {
        std::cerr << "Пользователь '" << username << "' не найден" << std::endl;
        return false;
    }
    
    return database_->delete_user(username);
}

TotpVerifyResult UserService::verify_totp(const std::string& username, const std::string& totp_code) {
    TotpVerifyResult result;
    result.success = false;
    result.access_granted = false;
    
    if (username.empty() || totp_code.empty()) {
        result.message = "Имя пользователя и TOTP код не могут быть пустыми";
        return result;
    }
    
    // Получаем пользователя
    std::unique_ptr<User> user = get_user(username);
    if (!user) {
        result.message = "Пользователь не найден";
        return result;
    }
    
    // Проверяем срок действия секрета
    if (database_->is_secret_expired(user->secret_expires_at)) {
        result.message = "Срок действия секрета истек";
        return result;
    }
    
    // Проверяем наличие секрета
    if (user->totp_secret.empty()) {
        result.message = "Секрет не установлен";
        return result;
    }
    
    try {
        // Расшифровываем секрет
        std::string secret_plain = crypto_service_->decrypt(user->totp_secret, username);
        if (secret_plain.empty()) {
            result.message = "Ошибка расшифровки секрета";
            return result;
        }
        
        // Создаем TOTP генератор и проверяем код
        TOTPGenerator totp(secret_plain);
        if (totp.verify_totp(totp_code, 1)) { // окно в 1 период (30 сек)
            result.success = true;
            result.access_granted = true;
            result.message = "Доступ разрешен";
        } else {
            result.message = "Неверный TOTP код";
        }
        
    } catch (const std::exception& e) {
        result.message = "Ошибка при верификации TOTP: " + std::string(e.what());
    }
    
    return result;
}

std::unique_ptr<User> UserService::get_user(const std::string& username) {
    if (username.empty()) {
        return nullptr;
    }
    
    return database_->get_user(username);
}

bool UserService::user_exists(const std::string& username) {
    if (username.empty()) {
        return false;
    }
    
    return database_->user_exists(username);
}
