from datetime import datetime
import captcha
import os
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from PIL import Image
from pathlib import Path

# selenium (https://www.selenium.dev/documentation/en/webdriver/browser_manipulation/)


class ChromeDriverManager():
    def __init__(self, driver, wait, logger):
        self.driver, self.wait, self.logger = driver, wait, logger

    def get_cracked_string_by_xpath(self, xpath):
        self.logger.debug(f"start to capture capcha image")
        CAPTCHA_IMG_PATH = f"capcha_data/capcha_{datetime.now().strftime('%m-%d %H:%M:%S')}.png"
        Path(CAPTCHA_IMG_PATH).parent.mkdir(parents=True, exist_ok=True)
        captcha_img_element = self.driver.find_element_by_xpath(xpath)
        with open(CAPTCHA_IMG_PATH, "wb") as f:
            f.write(captcha_img_element.screenshot_as_png)
        self.logger.debug(f"start to convert capcha to string")
        captcha_str = captcha.captcha_to_string(Image.open(CAPTCHA_IMG_PATH))
        self.logger.debug(f"captcha convert result: {captcha_str}")
        return captcha_str

    def find_and_click_by_xpath(self, xpath):
        try:
            # element = self.wait.until(
            #     ec.presence_of_element_located((By.XPATH, xpath)))
            element = self.driver.find_element_by_xpath(xpath)
            self.driver.execute_script("arguments[0].click();", element)
        except:
            raise
