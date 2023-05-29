from pages import locators, element
from pages.locators import MainPageLocators
from selenium.webdriver.common.by import By

class BasePage(object):
    """Base class to initialize the base page that will be called from all
    pages"""

    def __init__(self, driver):
        self.driver = driver

    def is_title_matches(self, expected_text):
        """Verifies that the hardcoded text "Python" appears in page title"""

        return expected_text in self.driver.title     


class MainPage(BasePage):
    """Home page action methods come here. I.e. Python.org"""

    def find_all_left_nav_items(self):
        """Triggers the search"""

        parent = self.driver.find_element(MainPageLocators.NAV_LEFT_PARENT[0], MainPageLocators.NAV_LEFT_PARENT[1])
        print(f"Parent Item: {parent.text}")
        children = parent.find_elements(By.TAG_NAME, "li")
 
        return children      
