from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class DriverManager:
    def __init__(self, binary_location=None, driver_path=None):
        self.binary_location = binary_location
        self.driver_path = driver_path
        self.driver = None

    def get_driver(self, headless=True):
        options = Options()

        if self.binary_location:
            options.binary_location = self.binary_location

        options.add_argument('--no-sandbox')
        options.add_argument('--single-process')
        options.add_argument('--disable-dev-shm-usage')
        if headless:
            options.add_argument('--headless')

        if self.binary_location and self.driver_path:  # Assume lambda environment setup
            self.driver = webdriver.Chrome(self.driver_path, options=options)
        else:
            # For development environment, use ChromeDriverManager
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

        return self.driver

    def close_driver(self):
        if self.driver:
            self.driver.close()
            self.driver.quit()
            self.driver = None
