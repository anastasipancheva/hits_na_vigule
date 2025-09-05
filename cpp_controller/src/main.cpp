#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include "user_service.h"
#include "totp.h"

class TOTPController {
private:
    std::unique_ptr<UserService> user_service_;

public:
    TOTPController() : user_service_(std::make_unique<UserService>()) {}

    void run() {
        std::cout << "=== TOTP Controller ===" << std::endl;
        std::cout << "Система управления TOTP секретами" << std::endl;
        std::cout << "Введите 'help' для списка команд" << std::endl;
        std::cout << std::endl;

        std::string input;
        while (true) {
            std::cout << "> ";
            std::getline(std::cin, input);
            
            if (input.empty()) continue;
            
            std::vector<std::string> args = split_input(input);
            if (args.empty()) continue;
            
            std::string command = args[0];
            
            if (command == "help" || command == "h") {
                show_help();
            } else if (command == "quit" || command == "exit" || command == "q") {
                std::cout << "До свидания!" << std::endl;
                break;
            } else if (command == "create_user" || command == "cu") {
                handle_create_user(args);
            } else if (command == "save_secret" || command == "ss") {
                handle_save_secret(args);
            } else if (command == "verify" || command == "v") {
                handle_verify_totp(args);
            } else if (command == "revoke" || command == "r") {
                handle_revoke_access(args);
            } else if (command == "delete_user" || command == "du") {
                handle_delete_user(args);
            } else if (command == "show_user" || command == "su") {
                handle_show_user(args);
            } else if (command == "generate_totp" || command == "gt") {
                handle_generate_totp(args);
            } else {
                std::cout << "Неизвестная команда: " << command << std::endl;
                std::cout << "Введите 'help' для списка команд" << std::endl;
            }
        }
    }

private:
    std::vector<std::string> split_input(const std::string& input) {
        std::vector<std::string> result;
        std::istringstream iss(input);
        std::string token;
        
        while (iss >> token) {
            result.push_back(token);
        }
        
        return result;
    }

    void show_help() {
        std::cout << "\nДоступные команды:" << std::endl;
        std::cout << "  create_user <username>     - Создать пользователя" << std::endl;
        std::cout << "  save_secret <username> <secret> - Сохранить TOTP секрет" << std::endl;
        std::cout << "  verify <username> <code>   - Проверить TOTP код" << std::endl;
        std::cout << "  revoke <username>          - Отозвать доступ пользователя" << std::endl;
        std::cout << "  delete_user <username>     - Удалить пользователя" << std::endl;
        std::cout << "  show_user <username>       - Показать информацию о пользователе" << std::endl;
        std::cout << "  generate_totp <secret>     - Сгенерировать TOTP код" << std::endl;
        std::cout << "  help                       - Показать эту справку" << std::endl;
        std::cout << "  quit                       - Выйти из программы" << std::endl;
        std::cout << std::endl;
        std::cout << "Сокращения: cu, ss, v, r, du, su, gt, h, q" << std::endl;
        std::cout << std::endl;
    }

    void handle_create_user(const std::vector<std::string>& args) {
        if (args.size() != 2) {
            std::cout << "Использование: create_user <username>" << std::endl;
            return;
        }
        
        const std::string& username = args[1];
        if (user_service_->create_user(username)) {
            std::cout << "Пользователь '" << username << "' успешно создан" << std::endl;
        } else {
            std::cout << "Ошибка создания пользователя '" << username << "'" << std::endl;
        }
    }

    void handle_save_secret(const std::vector<std::string>& args) {
        if (args.size() != 3) {
            std::cout << "Использование: save_secret <username> <secret>" << std::endl;
            return;
        }
        
        const std::string& username = args[1];
        const std::string& secret = args[2];
        
        if (user_service_->save_user_secret(username, secret)) {
            std::cout << "Секрет для пользователя '" << username << "' успешно сохранен" << std::endl;
        } else {
            std::cout << "Ошибка сохранения секрета для пользователя '" << username << "'" << std::endl;
        }
    }

    void handle_verify_totp(const std::vector<std::string>& args) {
        if (args.size() != 3) {
            std::cout << "Использование: verify <username> <code>" << std::endl;
            return;
        }
        
        const std::string& username = args[1];
        const std::string& code = args[2];
        
        TotpVerifyResult result = user_service_->verify_totp(username, code);
        
        if (result.success && result.access_granted) {
            std::cout << "✓ " << result.message << std::endl;
        } else {
            std::cout << "✗ " << result.message << std::endl;
        }
    }

    void handle_revoke_access(const std::vector<std::string>& args) {
        if (args.size() != 2) {
            std::cout << "Использование: revoke <username>" << std::endl;
            return;
        }
        
        const std::string& username = args[1];
        if (user_service_->revoke_user_access(username)) {
            std::cout << "Доступ для пользователя '" << username << "' отозван" << std::endl;
        } else {
            std::cout << "Ошибка отзыва доступа для пользователя '" << username << "'" << std::endl;
        }
    }

    void handle_delete_user(const std::vector<std::string>& args) {
        if (args.size() != 2) {
            std::cout << "Использование: delete_user <username>" << std::endl;
            return;
        }
        
        const std::string& username = args[1];
        std::cout << "Вы уверены, что хотите удалить пользователя '" << username << "'? (y/N): ";
        
        std::string confirmation;
        std::getline(std::cin, confirmation);
        
        if (confirmation == "y" || confirmation == "Y" || confirmation == "yes") {
            if (user_service_->delete_user(username)) {
                std::cout << "Пользователь '" << username << "' удален" << std::endl;
            } else {
                std::cout << "Ошибка удаления пользователя '" << username << "'" << std::endl;
            }
        } else {
            std::cout << "Удаление отменено" << std::endl;
        }
    }

    void handle_show_user(const std::vector<std::string>& args) {
        if (args.size() != 2) {
            std::cout << "Использование: show_user <username>" << std::endl;
            return;
        }
        
        const std::string& username = args[1];
        std::unique_ptr<User> user = user_service_->get_user(username);
        
        if (!user) {
            std::cout << "Пользователь '" << username << "' не найден" << std::endl;
            return;
        }
        
        std::cout << "\nИнформация о пользователе:" << std::endl;
        std::cout << "  ID: " << user->id << std::endl;
        std::cout << "  Имя: " << user->username << std::endl;
        std::cout << "  Секрет установлен: " << (user->totp_secret.empty() ? "Нет" : "Да") << std::endl;
        std::cout << "  Создан: " << user->created_at << std::endl;
        if (!user->secret_expires_at.empty()) {
            std::cout << "  Секрет истекает: " << user->secret_expires_at << std::endl;
        }
        std::cout << std::endl;
    }

    void handle_generate_totp(const std::vector<std::string>& args) {
        if (args.size() != 2) {
            std::cout << "Использование: generate_totp <secret>" << std::endl;
            return;
        }
        
        const std::string& secret = args[2];
        try {
            TOTPGenerator totp(secret);
            std::string code = totp.generate_totp();
            if (!code.empty()) {
                std::cout << "TOTP код: " << code << std::endl;
            } else {
                std::cout << "Ошибка генерации TOTP кода" << std::endl;
            }
        } catch (const std::exception& e) {
            std::cout << "Ошибка: " << e.what() << std::endl;
        }
    }
};

int main() {
    try {
        TOTPController controller;
        controller.run();
    } catch (const std::exception& e) {
        std::cerr << "Критическая ошибка: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
