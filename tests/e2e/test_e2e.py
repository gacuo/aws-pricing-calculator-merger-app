"""
E2Eテスト

実際のユーザーフローを自動テストします。
"""

import pytest
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# テスト用のURLとデータ
TEST_URL = os.environ.get('TEST_APP_URL', 'http://localhost:5000')
TEST_CALCULATOR_URLS = [
    "https://calculator.aws/#/estimate?id=test123456",
    "https://calculator.aws/#/estimate?id=test789012"
]


class TestE2EUserFlow:
    """E2Eテスト: ユーザーフロー検証"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス実行前の準備"""
        # Seleniumの設定
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(10)
    
    @classmethod
    def teardown_class(cls):
        """テストクラス実行後のクリーンアップ"""
        cls.driver.quit()
    
    def setup_method(self):
        """各テスト実行前の準備"""
        self.driver.get(TEST_URL)
    
    def test_homepage_loads(self):
        """ホームページが正常に読み込まれることを確認"""
        # タイトルの検証
        assert "AWS Pricing Calculator 見積もり合算ツール" in self.driver.title
        
        # 主要コンポーネントが表示されていることを確認
        assert self.driver.find_element(By.ID, "mergeForm").is_displayed()
        assert self.driver.find_element(By.ID, "addUrlBtn").is_displayed()
        assert self.driver.find_element(By.ID, "mergeBtn").is_displayed()
    
    def test_add_url_button_works(self):
        """「URLを追加」ボタンが正常に機能することを確認"""
        # 初期状態で1つのURL入力欄があることを確認
        url_inputs = self.driver.find_elements(By.CLASS_NAME, "url-input")
        assert len(url_inputs) == 1
        
        # 「URLを追加」ボタンをクリック
        add_url_btn = self.driver.find_element(By.ID, "addUrlBtn")
        add_url_btn.click()
        
        # URL入力欄が2つになっていることを確認
        url_inputs = self.driver.find_elements(By.CLASS_NAME, "url-input")
        assert len(url_inputs) == 2
        
        # さらにもう一度追加
        add_url_btn.click()
        url_inputs = self.driver.find_elements(By.CLASS_NAME, "url-input")
        assert len(url_inputs) == 3
    
    def test_remove_url_button_works(self):
        """「削除」ボタンが正常に機能することを確認"""
        # まず「URLを追加」ボタンで入力欄を追加
        add_url_btn = self.driver.find_element(By.ID, "addUrlBtn")
        add_url_btn.click()
        
        # URL入力欄が2つになっていることを確認
        url_inputs = self.driver.find_elements(By.CLASS_NAME, "url-input")
        assert len(url_inputs) == 2
        
        # 「削除」ボタンをクリック
        remove_btns = self.driver.find_elements(By.CLASS_NAME, "remove-url-btn")
        remove_btns[0].click()
        
        # URL入力欄が1つになっていることを確認
        url_inputs = self.driver.find_elements(By.CLASS_NAME, "url-input")
        assert len(url_inputs) == 1
    
    def test_form_validation(self):
        """フォームのバリデーションが正常に機能することを確認"""
        # 空のフォームを送信
        merge_btn = self.driver.find_element(By.ID, "mergeBtn")
        merge_btn.click()
        
        # HTMLのバリデーションにより送信が阻止されることを確認
        # (テストが次のステップに進むことで暗黙的に検証)
        
        # 無効なURLを入力
        url_input = self.driver.find_element(By.CLASS_NAME, "url-input")
        url_input.send_keys("https://invalid-url.com")
        
        # フォームを送信
        merge_btn.click()
        
        # エラーメッセージが表示されることを確認
        wait = WebDriverWait(self.driver, 10)
        try:
            error_msg = wait.until(EC.visibility_of_element_located((By.ID, "errorMessage")))
            assert "無効なAWS Pricing Calculator URL" in error_msg.text
        except TimeoutException:
            pytest.fail("エラーメッセージが表示されませんでした")
    
    @pytest.mark.skip(reason="APIモックが必要なため、CI環境での自動テストではスキップ")
    def test_full_merge_flow(self):
        """完全な合算フローが正常に機能することを確認（モック使用）"""
        # モックAPIを使用するか、実際のAPIをスタブ化する必要があります
        
        # 1つ目のURL入力欄に値を設定
        url_inputs = self.driver.find_elements(By.CLASS_NAME, "url-input")
        url_inputs[0].send_keys(TEST_CALCULATOR_URLS[0])
        
        # 「URLを追加」ボタンをクリック
        add_url_btn = self.driver.find_element(By.ID, "addUrlBtn")
        add_url_btn.click()
        
        # 2つ目のURL入力欄に値を設定
        url_inputs = self.driver.find_elements(By.CLASS_NAME, "url-input")
        url_inputs[1].send_keys(TEST_CALCULATOR_URLS[1])
        
        # フォームを送信
        merge_btn = self.driver.find_element(By.ID, "mergeBtn")
        merge_btn.click()
        
        # ローディング表示を確認
        loader = self.driver.find_element(By.ID, "loader")
        assert loader.is_displayed()
        
        # 結果が表示されるのを待機
        wait = WebDriverWait(self.driver, 15)
        try:
            result_container = wait.until(EC.visibility_of_element_located((By.ID, "resultContainer")))
            assert result_container.is_displayed()
            
            # 結果の内容を検証
            estimate_name = self.driver.find_element(By.ID, "estimateName").text
            assert estimate_name != ""
            
            monthly_cost = self.driver.find_element(By.ID, "monthlyCost").text
            assert monthly_cost != ""
            
            merged_url = self.driver.find_element(By.ID, "mergedUrl").text
            assert "calculator.aws/#/estimate?id=" in merged_url
            
        except TimeoutException:
            pytest.fail("結果が表示されませんでした")
