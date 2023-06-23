from selenium.webdriver.common.by import By

class MainPageLocators(object):
    """A class for main page locators. All main page locators should come here"""
    """ url: `/`"""
    CONTENT_HEADING = (By.ID, "index-content-heading")
    CONTENT_MESSAGE = (By.ID, "index-content-message")
    SEARCH_FORM = (By.ID, "index-content-search-form")

    NAV_LEFT_PARENT = (By.XPATH, "//*[@id='uk-nav-left']/ul")
    NAV_RIGHT_PARENT = (By.XPATH, "//*[@id='uk-nav-right']/ul")

    FOOTER = (By.ID, "ourchive-footer")

class SearchResultsPageLocators(object):
    """A class for search results locators. All search results locators should
    come here"""

    pass


class MainPageLoginLocators(object):

    LOGIN_USERNAME_INPUT = (By.ID, "login-username-input")
    LOGIN_PASSWORD_INPUT = (By.ID, "login-password-input")
    LOGIN_SUBMIT_BUTTON= (By.ID, "login-submit-button")
    LOGIN_UNSUCCESSFUL = (By.ID, "login-unsuccessful-error")
    