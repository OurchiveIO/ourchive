from selenium.webdriver.common.by import By

class MainPageLocators(object):
    """A class for main page locators. All main page locators should come here"""
    """ url: `/`"""
    TITLE_TEXT = (By.XPATH, "//*[@class='uk-first-column']/h1")
    TOPNAV_ITEMS = (By.XPATH, "//*[@class='uk-navbar-nav']/li")
    SIDENAV_ITEMS = (By.XPATH, "//*[@id='sidenav']/*/*/li")

class SearchResultsPageLocators(object):
    """A class for search results locators. All search results locators should
    come here"""

    pass