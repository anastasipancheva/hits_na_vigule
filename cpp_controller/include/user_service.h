#pragma once

#include <string>
#include <memory>
#include "database.h"
#include "crypto.h"
#include "totp.h"

struct TotpVerifyResult {
    bool success;
    std::string message;
    bool access_granted;
};

class UserService {
public:
    UserService();
    ~UserService();

    // Управление пользователями
    bool create_user(const std::string& username);
    bool save_user_secret(const std::string& username, const std::string& secret_plain);
    bool revoke_user_access(const std::string& username);
    bool delete_user(const std::string& username);
    
    // Верификация TOTP
    TotpVerifyResult verify_totp(const std::string& username, const std::string& totp_code);
    
    // Утилиты
    std::unique_ptr<User> get_user(const std::string& username);
    bool user_exists(const std::string& username);

private:
    std::unique_ptr<Database> database_;
    std::unique_ptr<CryptoService> crypto_service_;
};
