import pytest
from pages import page
# selenium 4
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as BraveService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

def test_driver():
    driver = webdriver.Chrome(service=BraveService(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install()))

    main_page = page.MainPage(driver)
    driver.get('https://ourchive-dev.stopthatimp.net/')
    assert main_page.is_title_matches("Ourchive") is True, "expected page title to contain 'Ourchive' and it did not."
   
    left_nav = main_page.find_all_left_nav_items()

    print("Found %s side nav items" % (len(left_nav)))
    for item in left_nav:
        print(item)