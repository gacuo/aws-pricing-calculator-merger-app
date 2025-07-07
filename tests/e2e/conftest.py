"""
E2Eテスト用の設定ファイル
"""

import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture(scope="session")
def selenium_driver():
    """Seleniumドライバーのセットアップ"""
    
    # CI環境かどうかを判断
    is_ci = os.environ.get('CI', 'false').lower() == 'true'
    
    # ChromeOptionsの設定
    options = webdriver.ChromeOptions()
    
    # CI環境の場合はヘッドレスモードで実行
    if is_ci:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
    
    # ドライバーのセットアップ
    # CI環境ではパスからドライバーを取得、ローカル環境ではwebdriver_managerを使用
    if is_ci:
        driver = webdriver.Chrome(options=options)
    else:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    
    # ウィンドウサイズの設定
    driver.set_window_size(1280, 1024)
    
    # 暗黙的な待機時間の設定
    driver.implicitly_wait(10)
    
    # フィクスチャーの提供
    yield driver
    
    # テスト終了後にドライバーを閉じる
    driver.quit()


@pytest.fixture
def app_url():
    """テスト対象アプリケーションのURL"""
    return os.environ.get('TEST_APP_URL', 'http://localhost:5000')
