class AccessReader {
    constructor() {
        this.qrScanner = null;
        this.QrScanner = null;
        // Начинаем инициализацию сразу
        this.init();
    }

    async init() {
        console.log('Инициализация считывателя доступа...');
        // Дожидаемся загрузки сканера перед выполнением других действий
        await this.loadQrScanner();
        this.setupTabs();
        this.setupFileUpload();
    }

async loadQrScanner() {
        try {
            // Если QR Scanner уже доступен, используем его
            if (typeof window.QrScanner !== 'undefined') {
                this.QrScanner = window.QrScanner;
                console.log('QR Scanner library already loaded.');
                const overlay = document.getElementById('qr-overlay');
                if (overlay) {
                    overlay.classList.add('hidden');
                }
                return;
            }

            // Создаём тег script для загрузки библиотеки
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/qr-scanner@1.4.2/qr-scanner.min.js';
            document.head.appendChild(script);

            // Создаём Promise, чтобы дождаться загрузки
            await new Promise((resolve, reject) => {
                script.onload = () => {
                    if (typeof window.QrScanner !== 'undefined') {
                        this.QrScanner = window.QrScanner;
                        console.log('QR Scanner library loaded successfully.');
                        const overlay = document.getElementById('qr-overlay');
                        if (overlay) {
                            overlay.classList.add('hidden');
                        }
                        resolve();
                    } else {
                        reject(new Error('QR Scanner not defined after loading'));
                    }
                };
                script.onerror = () => reject(new Error('Failed to load QR Scanner script'));
            });

        } catch (error) {
            console.error('Failed to load QR Scanner:', error);
            this.showError('Не удалось загрузить QR сканер. Проверьте подключение к интернету.');
            const overlay = document.getElementById('qr-overlay');
            if (overlay) {
                overlay.innerHTML = `
                    <div class="text-white text-center">
                        <div class="text-2xl mb-2">❌</div>
                        <p>Ошибка загрузки сканера</p>
                        <p class="text-sm mt-1">Используйте загрузку файлов</p>
                    </div>
                `;
            }
        }
    }

    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    async switchTab(tabName) {
        // Обновляем активные кнопки
        document.querySelectorAll('.tab-button').forEach(btn => {
            const isActive = btn.dataset.tab === tabName;
            btn.setAttribute('data-active', isActive);
        });

        // Показываем активный контент
        document.querySelectorAll('.tab-content').forEach(content => {
            const isActive = content.id === `${tabName}-tab`;
            content.classList.toggle('hidden', !isActive);
            content.classList.toggle('active', isActive);
        });

        // Останавливаем предыдущие процессы
        this.stopQRScanner();

        // Запускаем процессы для активного таба
        if (tabName === 'qr') {
            await this.startQRScanner();
        }
    }

    async startQRScanner() {
        try {
            const video = document.getElementById('qr-video');
            const overlay = document.getElementById('qr-overlay');

            if (!video || !this.QrScanner) {
                this.showError('QR сканер не доступен');
                return;
            }

            // Показываем индикатор загрузки
            if (overlay) {
                overlay.classList.remove('hidden');
                overlay.innerHTML = `
                    <div class="text-white text-center">
                        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-2"></div>
                        <p>Запуск камеры...</p>
                    </div>
                `;
            }

            // Инициализируем QR сканер
            this.qrScanner = new this.QrScanner(
                video,
                result => this.handleQRResult(result),
                {
                    onDecodeError: (error) => {
                        // Игнорируем обычные ошибки "QR code not found"
                        if (!error.includes('No QR code found')) {
                            console.log('QR scanning error:', error);
                        }
                    },
                    highlightScanRegion: true,
                    highlightCodeOutline: true,
                }
            );

            await this.qrScanner.start();
            console.log('QR сканер запущен');

            // Скрываем индикатор загрузки
            if (overlay) {
                overlay.classList.add('hidden');
            }

        } catch (error) {
            console.error('Ошибка запуска QR сканера:', error);

            const overlay = document.getElementById('qr-overlay');
            if (overlay) {
                overlay.innerHTML = `
                    <div class="text-white text-center">
                        <div class="text-2xl mb-2">❌</div>
                        <p>Ошибка доступа к камере</p>
                        <p class="text-sm mt-1">Проверьте разрешения или используйте файлы</p>
                    </div>
                `;
            }

            this.showError('Не удалось запустить камеру. Проверьте разрешения.');
        }
    }

    stopQRScanner() {
        if (this.qrScanner) {
            this.qrScanner.stop();
            this.qrScanner.destroy();
            this.qrScanner = null;
            console.log('QR сканер остановлен');
        }
    }

    handleQRResult(result) {
        console.log('QR код распознан:', result);

        // Извлекаем только цифры из QR кода
        const digits = result.data.replace(/\D/g, '');

        if (digits.length === 6) {
            this.submitCode(digits, 'qr');
            this.stopQRScanner();
        } else {
            this.showError(`QR код содержит не 6 цифр: ${digits}`);
        }
    }

    setupFileUpload() {
        const fileInput = document.getElementById('qr-file');
        if (!fileInput) return;

        fileInput.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                this.scanQRFromFile(file);
            }
        });
    }

    async scanQRFromFile(file) {
        try {
            const overlay = document.getElementById('qr-overlay');
            if (overlay) {
                overlay.classList.remove('hidden');
                overlay.innerHTML = `
                    <div class="text-white text-center">
                        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-2"></div>
                        <p>Сканирование файла...</p>
                    </div>
                `;
            }

            if (!this.QrScanner) {
                throw new Error('QR Scanner not loaded');
            }

            // Создаем URL для файла
            const imageUrl = URL.createObjectURL(file);

            // Сканируем изображение
            const result = await this.QrScanner.scanImage(imageUrl);

            URL.revokeObjectURL(imageUrl); // Очищаем URL

            if (overlay) {
                overlay.classList.add('hidden');
            }

            if (result) {
                this.handleQRResult({ data: result });
            } else {
                this.showError('Не удалось распознать QR код в изображении');
            }

        } catch (error) {
            console.error('Ошибка сканирования файла:', error);

            const overlay = document.getElementById('qr-overlay');
            if (overlay) {
                overlay.classList.add('hidden');
            }

            this.showError('Не удалось распознать QR код: ' + error.message);
        }
    }

    submitCode(code, method) {
        // Используем htmx для отправки
        htmx.ajax('POST', '/reader/verify-code', {
            values: {
                code: code,
                method: method
            },
            target: '#result-container'
        });
    }

    showError(message) {
        // Создаем временное сообщение об ошибке
        const errorDiv = document.createElement('div');
        errorDiv.className = 'p-3 mb-4 bg-red-100 border border-red-400 text-red-700 rounded';
        errorDiv.textContent = message;

        const container = document.getElementById('result-container');
        if (container) {
            container.prepend(errorDiv);
            // Автоудаление через 5 секунд
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.parentNode.removeChild(errorDiv);
                }
            }, 5000);
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.accessReader = new AccessReader();
});