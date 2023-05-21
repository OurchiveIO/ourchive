import pytest
# selenium 4
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as BraveService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType


def test_driver():
    driver = webdriver.Chrome(service=BraveService(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install()))

    driver.get('http://127.0.0.1:8000/')
    assert 'Ourchive' in driver.title

    nav = driver.find_element(By.CLASS_NAME, 'ourchive-navbar')
    print(nav)