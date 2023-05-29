import pytest
from pages import page
# selenium 4
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as BraveService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

def test_driver():
    driver = webdriver.Chrome(service=BraveService(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install()))

    main_page = page.MainPage(driver)
    driver.get('http://127.0.0.1:8000/')
    assert 'Ourchive' in driver.title
    assert main_page.is_title_matches(), "python.org title doesn't match."
   
    sidenav = main_page.find_all_sidenav_items()
    print("Found %s side nav items" % (len(sidenav)))
    for item in sidenav:
        print(item)