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
class TestInvalidUserFlows:


    driverLogger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    driverLogger.setLevel(logging.NOTSET) 

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


    def test_cannot_login_with_empty_credentials(self):
        login_page = page.MainPageLogin(self.driver)
        self.driver.get(login_page.page_url)
        assert login_page.is_title_matches("Log In") is True, "expected page title to contain `Log In` and it did not."
       
        login_page.validate_page_load()

        username_input = self.driver.find_element(MainPageLoginLocators.LOGIN_USERNAME_INPUT[0], MainPageLoginLocators.LOGIN_USERNAME_INPUT[1])
        logging.getLogger().info("username input text: {!r}".format(username_input.get_property('value')))
        password_input = self.driver.find_element(MainPageLoginLocators.LOGIN_PASSWORD_INPUT[0], MainPageLoginLocators.LOGIN_PASSWORD_INPUT[1])
        logging.getLogger().info("password_input text: {!r}".format(password_input.get_property('value')))
        
        assert len(username_input.get_property('value')) == 0, "Expected Username Input Value to be empty"
        assert len(password_input.get_property('value')) == 0, "Expected Password Input Value to be empty"

        logging.getLogger().info("Now we submit the form...")

        login_page.submit_login_form()

        logging.getLogger().info("We should get a pop up with a login unsuccessful message!")
        assert login_page.validate_unsuccessful_login(logging), "Expected to get Unsuccessful Login Message"

        logging.getLogger().info("After an unsuccessful login, the form values should be cleared out.")
        username_input_post = self.driver.find_element(MainPageLoginLocators.LOGIN_USERNAME_INPUT[0], MainPageLoginLocators.LOGIN_USERNAME_INPUT[1])
        logging.getLogger().info("username input text: {!r}".format(username_input_post.get_property('value')))
        password_input_post = self.driver.find_element(MainPageLoginLocators.LOGIN_PASSWORD_INPUT[0], MainPageLoginLocators.LOGIN_PASSWORD_INPUT[1])
        logging.getLogger().info("password_input text: {!r}".format(password_input_post.get_property('value')))
        
        assert len(username_input_post.get_property('value')) == 0, "Expected Username Input Value to be empty"
        assert len(password_input_post.get_property('value')) == 0, "Expected Password Input Value to be empty"

        

    def test_cannot_login_with_invalid_credentials(self):
        login_page = page.MainPageLogin(self.driver)
        self.driver.get(login_page.page_url)
        assert login_page.is_title_matches("Log In") is True, "expected page title to contain `Log In` and it did not."
        
        logging.getLogger().info("step 1: filling in login form with random gibberish username and password.")

        invalid_username = 'asdjgiasjijwes'
        invalid_password = 'gV7hDHXQmonUgdF'
        login_page.validate_page_load()
        login_page.fill_login_form(invalid_username, invalid_password)

        logging.getLogger().info("We expect the form inputs to have value after fill but before submission...")

        username_input = self.driver.find_element(MainPageLoginLocators.LOGIN_USERNAME_INPUT[0], MainPageLoginLocators.LOGIN_USERNAME_INPUT[1])
        logging.getLogger().info("username input text: {!r}".format(username_input.get_property('value')))
        password_input = self.driver.find_element(MainPageLoginLocators.LOGIN_PASSWORD_INPUT[0], MainPageLoginLocators.LOGIN_PASSWORD_INPUT[1])
        logging.getLogger().info("password_input text: {!r}".format(password_input.get_property('value')))
        
        assert len(username_input.get_property('value')) > 0, "Expected Username Input Value Before Submission to not be empty"
        assert len(password_input.get_property('value')) > 0, "Expected Password Input Value Before Submission to not be empty"

        logging.getLogger().info("Now we submit the form...")

        login_page.submit_login_form()

        logging.getLogger().info("We should get a pop up with a login unsuccessful message!")
        assert login_page.validate_unsuccessful_login(logging), "Expected to get Unsuccessful Login Message"

        logging.getLogger().info("After an unsuccessful login, the form values should be cleared out.")
        username_input_post = self.driver.find_element(MainPageLoginLocators.LOGIN_USERNAME_INPUT[0], MainPageLoginLocators.LOGIN_USERNAME_INPUT[1])
        logging.getLogger().info("username input text: {!r}".format(username_input_post.get_property('value')))
        password_input_post = self.driver.find_element(MainPageLoginLocators.LOGIN_PASSWORD_INPUT[0], MainPageLoginLocators.LOGIN_PASSWORD_INPUT[1])
        logging.getLogger().info("password_input text: {!r}".format(password_input_post.get_property('value')))
        
        assert len(username_input_post.get_property('value')) == 0, "Expected Username Input Value to be empty"
        assert len(password_input_post.get_property('value')) == 0, "Expected Password Input Value to be empty"

        