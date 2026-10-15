import time
import random
import shutil
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class StealthSeleniumBot:
    def __init__(self, user_data_dir: str = "./browser_session", headless: bool = True):
        self.user_data_dir: str = user_data_dir
        self.headless: bool = headless
        self.driver: webdriver.Chrome = self._init_driver()

    def _init_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        chrome_options.page_load_strategy = "eager"

        chrome_bin = (
            shutil.which("google-chrome") 
            or shutil.which("chrome") 
            or shutil.which("chromium") 
            or shutil.which("chromium-browser")
        )
        if chrome_bin:
            chrome_options.binary_location = chrome_bin

        if self.headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--remote-debugging-pipe")
        chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        
        exclude_switches: List[str] = ["enable-automation"]
        chrome_options.add_experimental_option("excludeSwitches", exclude_switches)  # type: ignore
        chrome_options.add_experimental_option("useAutomationExtension", False)  # type: ignore

        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(15)  # 15s page timeout prevents renderer deadlocks
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def human_delay(self, min_sec: float = 1.5, max_sec: float = 3.5) -> None:
        time.sleep(random.uniform(min_sec, max_sec))

    def close(self) -> None:
        self.driver.quit()