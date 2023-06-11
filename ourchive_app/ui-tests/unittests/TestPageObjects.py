import unittest
from pages import locators, element
from pages.page import BasePage, MainPage, MainPageLogin

class TestPageObjects(unittest.TestCase):

    _driver = "hello"

    def test_init(self):
        base_page = BasePage(self._driver)
        main_page = MainPage(self._driver)
        login_page = MainPageLogin(self._driver)

        print("base page base url: {!r}".format(base_page.ourchive_baseurl))
        print("base page url: {!r}".format(base_page.page_url))
        print("main page url: {!r}".format(main_page.page_url))
        print("login page url: {!r}".format(login_page.page_url))

        assert base_page.ourchive_baseurl in base_page.page_url, "Expected {!r} to contain {!r}".format(base_page.page_url, base_page.ourchive_baseurl)
        assert base_page.ourchive_baseurl in main_page.page_url , "Expected {!r} to contain {!r}".format(main_page.page_url, base_page.ourchive_baseurl)
        assert base_page.ourchive_baseurl in login_page.page_url , "Expected {!r} to contain {!r}".format(login_page.page_url, base_page.ourchive_baseurl)


if __name__ == '__main__':
    unittest.main()