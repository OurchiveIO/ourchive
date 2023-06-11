import pytest
from selenium.webdriver.edge.webdriver import WebDriver
from pages import page
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as BraveService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture
def setup_and_teardown_for_driver(request):
    print("\ntest setup:")
    driver = webdriver.Chrome(service=BraveService(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install()))
    driver.maximize_window()
    request.cls.driver = driver
    yield
    print("\ntest teardown")
    driver.close()

'''
tests for a valid user
'''
@pytest.mark.usefixtures("setup_and_teardown_for_driver")
class TestValidUserFlows:

    def test_can_load_landingpage(self):

        main_page = page.MainPage(self.driver)
        self.driver.get(main_page.page_url)
        assert main_page.is_title_matches("Ourchive") is True, "expected page title to contain 'Ourchive' and it did not."
        
        left_nav = main_page.find_all_left_nav_items()

        #todo: add element exists checks


    def test_can_login(self):
        login_page = page.MainPageLogin(self.driver)
        self.driver.get(login_page.page_url)
        assert login_page.is_title_matches("Ourchive") is True, "expected page title to contain 'Ourchive' and it did not."
       
        login_page.validate_page_load()
