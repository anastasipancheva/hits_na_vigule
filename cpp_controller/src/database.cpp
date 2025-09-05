#include "database.h"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <random>
#include <chrono>
#include <ctime>

Database::Database(const std::string& db_path) : db_(nullptr) {
    if (sqlite3_open(db_path.c_str(), &db_) != SQLITE_OK) {
        std::cerr << "Ошибка открытия базы данных: " << sqlite3_errmsg(db_) << std::endl;
        return;
    }
    
    if (!initialize_database()) {
        std::cerr << "Ошибка инициализации базы данных" << std::endl;
    }
}

Database::~Database() {
    if (db_) {
        sqlite3_close(db_);
    }
}

bool Database::initialize_database() {
    const char* create_table_sql = R"(
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            totp_secret BLOB,
            secret_expires_at TEXT,
            created_at TEXT NOT NULL
        )
    )";
    
    char* err_msg = nullptr;
    if (sqlite3_exec(db_, create_table_sql, nullptr, nullptr, &err_msg) != SQLITE_OK) {
        std::cerr << "Ошибка создания таблицы: " << err_msg << std::endl;
        sqlite3_free(err_msg);
        return false;
    }
    
    return true;
}

std::string Database::generate_uuid() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 15);
    
    std::stringstream ss;
    ss << std::hex;
    for (int i = 0; i < 32; ++i) {
        if (i == 8 || i == 12 || i == 16 || i == 20) ss << "-";
        ss << dis(gen);
    }
    return ss.str();
}

std::string Database::get_current_time_iso() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto tm = *std::gmtime(&time_t);
    
    std::stringstream ss;
    ss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
    return ss.str();
}

bool Database::is_secret_expired(const std::string& expires_at) {
    if (expires_at.empty()) {
        return false; // Нет срока истечения
    }
    
    // Парсим ISO 8601 время
    std::tm tm = {};
    std::istringstream ss(expires_at);
    ss >> std::get_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
    
    if (ss.fail()) {
        return false; // Неверный формат, считаем не истекшим
    }
    
    auto expires_time = std::chrono::system_clock::from_time_t(std::mktime(&tm));
    auto now = std::chrono::system_clock::now();
    
    return now > expires_time;
}

bool Database::create_user(const std::string& username) {
    if (user_exists(username)) {
        return false; // Пользователь уже существует
    }
    
    std::string id = generate_uuid();
    std::string created_at = get_current_time_iso();
    
    const char* sql = "INSERT INTO users (id, username, created_at) VALUES (?, ?, ?)";
    sqlite3_stmt* stmt;
    
    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        std::cerr << "Ошибка подготовки запроса: " << sqlite3_errmsg(db_) << std::endl;
        return false;
    }
    
    sqlite3_bind_text(stmt, 1, id.c_str(), -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 2, username.c_str(), -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 3, created_at.c_str(), -1, SQLITE_STATIC);
    
    int result = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    
    return result == SQLITE_DONE;
}

bool Database::user_exists(const std::string& username) {
    const char* sql = "SELECT COUNT(*) FROM users WHERE username = ?";
    sqlite3_stmt* stmt;
    
    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        return false;
    }
    
    sqlite3_bind_text(stmt, 1, username.c_str(), -1, SQLITE_STATIC);
    
    int result = sqlite3_step(stmt);
    bool exists = false;
    
    if (result == SQLITE_ROW) {
        exists = sqlite3_column_int(stmt, 0) > 0;
    }
    
    sqlite3_finalize(stmt);
    return exists;
}

std::unique_ptr<User> Database::get_user(const std::string& username) {
    const char* sql = "SELECT id, username, totp_secret, secret_expires_at, created_at FROM users WHERE username = ?";
    sqlite3_stmt* stmt;
    
    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        return nullptr;
    }
    
    sqlite3_bind_text(stmt, 1, username.c_str(), -1, SQLITE_STATIC);
    
    std::unique_ptr<User> user = nullptr;
    int result = sqlite3_step(stmt);
    
    if (result == SQLITE_ROW) {
        user = std::make_unique<User>();
        user->id = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
        user->username = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 1));
        
        // Обработка BLOB данных
        const void* blob_data = sqlite3_column_blob(stmt, 2);
        int blob_size = sqlite3_column_bytes(stmt, 2);
        if (blob_data && blob_size > 0) {
            user->totp_secret.assign(
                static_cast<const uint8_t*>(blob_data),
                static_cast<const uint8_t*>(blob_data) + blob_size
            );
        }
        
        const char* expires_at = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 3));
        user->secret_expires_at = expires_at ? expires_at : "";
        
        user->created_at = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 4));
    }
    
    sqlite3_finalize(stmt);
    return user;
}

bool Database::update_user_secret(const std::string& username, const std::vector<uint8_t>& encrypted_secret) {
    const char* sql = "UPDATE users SET totp_secret = ? WHERE username = ?";
    sqlite3_stmt* stmt;
    
    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        return false;
    }
    
    sqlite3_bind_blob(stmt, 1, encrypted_secret.data(), encrypted_secret.size(), SQLITE_STATIC);
    sqlite3_bind_text(stmt, 2, username.c_str(), -1, SQLITE_STATIC);
    
    int result = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    
    return result == SQLITE_DONE;
}

bool Database::revoke_user_access(const std::string& username) {
    const char* sql = "UPDATE users SET totp_secret = NULL WHERE username = ?";
    sqlite3_stmt* stmt;
    
    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        return false;
    }
    
    sqlite3_bind_text(stmt, 1, username.c_str(), -1, SQLITE_STATIC);
    
    int result = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    
    return result == SQLITE_DONE;
}

bool Database::delete_user(const std::string& username) {
    const char* sql = "DELETE FROM users WHERE username = ?";
    sqlite3_stmt* stmt;
    
    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        return false;
    }
    
    sqlite3_bind_text(stmt, 1, username.c_str(), -1, SQLITE_STATIC);
    
    int result = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    
    return result == SQLITE_DONE;
}
