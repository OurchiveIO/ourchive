#conftest.py is for storing fixtures and pytest-plugins
# see: https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#conftest-py-plugins
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
import logging
import os




@pytest.fixture(scope='session')
def path_to_chrome():
    return ChromeDriverManager().install()

@pytest.fixture(scope='session')
def path_to_firefox():
    return GeckoDriverManager().install()


@pytest.fixture
def return_headless_chrome_driver(path_to_chrome, base_url, request):
    webdriver_service = ChromeService(executable_path=path_to_chrome)
    webdriver_service.start()

    options = webdriver.ChromeOptions()
    options.headless = True
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Remote(webdriver_service.service_url, options=options)

    request.cls.driver = driver
    driver.get(base_url)
    driver.maximize_window()
    yield
    driver.quit()

@pytest.fixture
def return_chrome_driver(path_to_chrome, base_url, request):
    """
        utilizes the webdriver_manager package to return a chrome webdriver
        config for selenium 4+
    """
    os.environ['WDM_LOG'] = str(logging.NOTSET)
    driver = webdriver.Chrome(service=ChromeService(executable_path=path_to_chrome))
    request.cls.driver = driver
    driver.get(base_url)
    driver.maximize_window()
    yield
    driver.quit()

@pytest.fixture
def return_firefox_driver(path_to_firefox, base_url, request):
    """
        utilizes the webdriver_manager package to return a firefox webdriver
        config for selenium 4+
    """
    os.environ['WDM_LOG'] = str(logging.NOTSET)
    driver = webdriver.Firefox(service=FirefoxService(executable_path=path_to_firefox))

    request.cls.driver = driver
    driver.get(base_url)
    driver.maximize_window()
    yield
    driver.quit()

