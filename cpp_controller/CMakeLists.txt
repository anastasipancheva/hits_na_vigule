cmake_minimum_required(VERSION 3.16)
project(TOTPController)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Поиск зависимостей
find_package(PkgConfig)
if(PKG_CONFIG_FOUND)
    pkg_check_modules(SQLITE3 sqlite3)
    pkg_check_modules(OPENSSL openssl)
    pkg_check_modules(CRYPTO libcrypto)
endif()

# Fallback поиск библиотек
if(NOT SQLITE3_FOUND)
    find_library(SQLITE3_LIBRARIES sqlite3)
    find_path(SQLITE3_INCLUDE_DIRS sqlite3.h)
endif()

if(NOT OPENSSL_FOUND)
    find_package(OpenSSL REQUIRED)
    set(OPENSSL_LIBRARIES ${OPENSSL_LIBRARIES})
    set(OPENSSL_INCLUDE_DIRS ${OPENSSL_INCLUDE_DIRS})
endif()

if(NOT CRYPTO_FOUND)
    find_library(CRYPTO_LIBRARIES crypto)
    find_path(CRYPTO_INCLUDE_DIRS openssl/evp.h)
endif()

# Включение директорий
if(SQLITE3_INCLUDE_DIRS)
    include_directories(${SQLITE3_INCLUDE_DIRS})
endif()
if(OPENSSL_INCLUDE_DIRS)
    include_directories(${OPENSSL_INCLUDE_DIRS})
endif()
if(CRYPTO_INCLUDE_DIRS)
    include_directories(${CRYPTO_INCLUDE_DIRS})
endif()

# Исходные файлы
set(SOURCES
    src/main.cpp
    src/database.cpp
    src/crypto.cpp
    src/totp.cpp
    src/user_service.cpp
)

# Заголовочные файлы
set(HEADERS
    include/database.h
    include/crypto.h
    include/totp.h
    include/user_service.h
)

# Включение директории с заголовками
include_directories(include)

# Создание исполняемого файла
add_executable(totp_controller ${SOURCES} ${HEADERS})

# Линковка библиотек
if(SQLITE3_LIBRARIES)
    target_link_libraries(totp_controller ${SQLITE3_LIBRARIES})
endif()
if(OPENSSL_LIBRARIES)
    target_link_libraries(totp_controller ${OPENSSL_LIBRARIES})
endif()
if(CRYPTO_LIBRARIES)
    target_link_libraries(totp_controller ${CRYPTO_LIBRARIES})
endif()

# Флаги компиляции
if(SQLITE3_CFLAGS_OTHER)
    target_compile_options(totp_controller PRIVATE ${SQLITE3_CFLAGS_OTHER})
endif()
if(OPENSSL_CFLAGS_OTHER)
    target_compile_options(totp_controller PRIVATE ${OPENSSL_CFLAGS_OTHER})
endif()
if(CRYPTO_CFLAGS_OTHER)
    target_compile_options(totp_controller PRIVATE ${CRYPTO_CFLAGS_OTHER})
endif()

# Установка
install(TARGETS totp_controller DESTINATION bin)
