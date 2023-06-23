import pytest
from selenium.webdriver.edge.webdriver import WebDriver
from pages import page
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.locators import MainPageLocators, MainPageLoginLocators
import logging
from webdriver_manager.core.logger import set_logger


'''
tests for a valid user
'''
@pytest.mark.usefixtures("return_headless_chrome_driver", "caplog")
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
        assert login_page.is_title_matches("Log In") is True, "expected page title to contain 'Log In' and it did not."
       
        login_page.validate_page_load()
        login_page.fill_login_form('kate', 'gV7hDHXQmonUgdF')

        username_input = self.driver.find_element(MainPageLoginLocators.LOGIN_USERNAME_INPUT[0], MainPageLoginLocators.LOGIN_USERNAME_INPUT[1])
        logging.getLogger().info("username input text: {!r}".format(username_input.get_property('value')))
        password_input = self.driver.find_element(MainPageLoginLocators.LOGIN_PASSWORD_INPUT[0], MainPageLoginLocators.LOGIN_PASSWORD_INPUT[1])
        logging.getLogger().info("password_input text: {!r}".format(password_input.get_property('value')))
        
        assert len(username_input.get_property('value')) > 0, "Expected Username Input Value to Be Greater Than 0"
        assert len(password_input.get_property('value')) > 0, "Expected Password Input Value to Be Greater Than 0"

        login_page.submit_login_form()

        submit_button = WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((MainPageLoginLocators.LOGIN_SUBMIT_BUTTON[0], MainPageLoginLocators.LOGIN_SUBMIT_BUTTON[1])))