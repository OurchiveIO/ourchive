import pytest
from selenium.webdriver.edge.webdriver import WebDriver
from pages import page
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from pages.locators import MainPageLocators, MainPageLoginLocators
import logging
from webdriver_manager.core.logger import set_logger


pytestmark = pytest.mark.nondestructive


'''
tests for a valid user
'''
@pytest.mark.usefixtures("return_chrome_driver", "caplog")
class TestValidUserFlows:


    logging.basicConfig(level=logging.DEBUG)
    testLogger = logging.getLogger()
    testLogger.setLevel(logging.INFO)
    testLogger.addHandler(logging.StreamHandler())
    testLogger.addHandler(logging.FileHandler("test.log"))

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
        login_page.fill_login_form('kate', 'gV7hDHXQmonUgdF')

        username_input = self.driver.find_element(MainPageLoginLocators.LOGIN_USERNAME_INPUT[0], MainPageLoginLocators.LOGIN_USERNAME_INPUT[1])
        logging.getLogger().info("username input text "+username_input.text)
        password_input = self.driver.find_element(MainPageLoginLocators.LOGIN_PASSWORD_INPUT[0], MainPageLoginLocators.LOGIN_PASSWORD_INPUT[1])
        logging.getLogger().info("password input text "+password_input.text)
        submit_button = self.driver.find_element(MainPageLoginLocators.LOGIN_SUBMIT_BUTTON[0], MainPageLoginLocators.LOGIN_SUBMIT_BUTTON[1])
