from pages import locators, element
from pages.locators import MainPageLocators, MainPageLoginLocators
from selenium.webdriver.common.by import By

class BasePage(object):
    """Base class to initialize the base page that will be called from all
    pages"""

    url_segment = "/"
    page_url = ""
    def __init__(self, driver):
        self.driver = driver
        self.ourchive_baseurl = "https://ourchive-dev.stopthatimp.net"
        self.page_url = self.ourchive_baseurl+self.url_segment

    def is_title_matches(self, expected_text):
        """Verifies that the hardcoded text "Python" appears in page title"""

        return expected_text in self.driver.title     


class MainPage(BasePage):
    """Home page action methods come here. I.e. Python.org"""

    url_segment = "/"

    def __init__(self, driver):
      super().__init__(driver)


    def find_all_left_nav_items(self):
        """Triggers the search"""

        parent = self.driver.find_element(MainPageLocators.NAV_LEFT_PARENT[0], MainPageLocators.NAV_LEFT_PARENT[1])
        print(f"Parent Item: {parent.text}")
        children = parent.find_elements(By.TAG_NAME, "li")
 
        return children      


class MainPageLogin(BasePage):
    """Home page action methods come here. I.e. Python.org"""
    url_segment = "/login"

    def __init__(self, driver):
      super().__init__(driver)

    def validate_page_load(self):
        """ validates that all login form elements load and take input as expected """
        
        username_input = self.driver.find_element(MainPageLoginLocators.LOGIN_USERNAME_INPUT[0], MainPageLoginLocators.LOGIN_USERNAME_INPUT[1])
        password_input = self.driver.find_element(MainPageLoginLocators.LOGIN_PASSWORD_INPUT[0], MainPageLoginLocators.LOGIN_PASSWORD_INPUT[1])
        submit_button = self.driver.find_element(MainPageLoginLocators.LOGIN_SUBMIT_BUTTON[0], MainPageLoginLocators.LOGIN_SUBMIT_BUTTON[1])


        assert username_input.is_displayed() is True, f"Expected Username Input Field is_displayed = true, however was: {username_input.is_displayed()}"
        assert username_input.is_enabled() is True, f"Expected Username Input Field is_enabled  = true, however was:  {username_input.is_enabled()}"
        assert username_input.is_selected() is True, f"Expected Username Input Field is_selected = true, however was:  {username_input.is_displayed()}"



    def fill_login_form(self, username: str, password: str):
        pass

