#!/usr/bin/env python3
"""
Скрипт для запуска Door Controller API
"""

import uvicorn
from controller.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
