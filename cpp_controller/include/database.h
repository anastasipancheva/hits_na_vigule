#pragma once

#include <string>
#include <vector>
#include <memory>
#include <sqlite3.h>

struct User {
    std::string id;
    std::string username;
    std::vector<uint8_t> totp_secret;  // Зашифрованный секрет
    std::string secret_expires_at;     // ISO 8601 строка или пустая
    std::string created_at;            // ISO 8601 строка
};

class Database {
public:
    Database(const std::string& db_path = "controller.db");
    ~Database();

    // Пользователи
    bool create_user(const std::string& username);
    bool user_exists(const std::string& username);
    std::unique_ptr<User> get_user(const std::string& username);
    bool update_user_secret(const std::string& username, const std::vector<uint8_t>& encrypted_secret);
    bool revoke_user_access(const std::string& username);
    bool delete_user(const std::string& username);
    
    // Утилиты
    std::string get_current_time_iso();
    bool is_secret_expired(const std::string& expires_at);

private:
    sqlite3* db_;
    bool initialize_database();
    std::string generate_uuid();
};
