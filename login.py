import os
import time
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from engine.bot import StealthSeleniumBot

load_dotenv("config/.env")

def automated_linkedin_login():
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password or email == "your_email@example.com":
        print("[ERROR] Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD inside config/.env first!", flush=True)
        return

    print("=" * 60, flush=True)
    print("STARTING HEADLESS LINKEDIN AUTHENTICATION", flush=True)
    print("=" * 60, flush=True)

    bot = StealthSeleniumBot(headless=True)
    wait = WebDriverWait(bot.driver, 12)
    
    try:
        print("Opening LinkedIn sign-in page...", flush=True)
        bot.driver.get("https://www.linkedin.com/login")
        bot.human_delay(2, 4)

        # Multi-selector strategy for email field
        email_selectors = [
            (By.ID, "username"),
            (By.NAME, "session_key"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[autocomplete='username']")
        ]

        email_field = None
        for by, selector in email_selectors:
            try:
                email_field = wait.until(EC.element_to_be_clickable((by, selector)))
                if email_field:
                    break
            except Exception:
                continue

        if not email_field:
            raise Exception("Could not locate email input field using any standard selector.")

        email_field.clear()
        for char in email:
            email_field.send_keys(char)
            time.sleep(0.04)
        
        # Multi-selector strategy for password field
        password_selectors = [
            (By.ID, "password"),
            (By.NAME, "session_password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[autocomplete='current-password']")
        ]

        password_field = None
        for by, selector in password_selectors:
            try:
                password_field = bot.driver.find_element(by, selector)
                if password_field:
                    break
            except Exception:
                continue

        if not password_field:
            raise Exception("Could not locate password input field using any standard selector.")

        password_field.clear()
        for char in password:
            password_field.send_keys(char)
            time.sleep(0.04)

        password_field.send_keys(Keys.RETURN)
        bot.human_delay(4, 6)

        current_url = bot.driver.current_url
        print(f"Current Page URL: {current_url}", flush=True)

        # Check if 2FA / CAPTCHA prompt is triggered
        if "challenge" in current_url or "pin" in current_url or "checkpoint" in current_url:
            print("\n[SECURITY CHECK] LinkedIn requires verification.", flush=True)
            pin_code = input("Enter the verification PIN/Code sent to your email or phone: ").strip()
            
            try:
                pin_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='pin'], input[id='input-auth-code'], input[type='text']"))
                )
                pin_input.send_keys(pin_code)
                pin_input.send_keys(Keys.RETURN)
                bot.human_delay(4, 6)
            except Exception as pin_err:
                print(f"Could not locate PIN input automatically: {pin_err}", flush=True)

        # Final Verification
        if any(keyword in bot.driver.current_url for keyword in ["feed", "check", "mynetwork", "jobs"]):
            print("\n✅ Successfully authenticated and saved session cookies to './browser_session'!", flush=True)
        else:
            print(f"\n⚠️ Form submitted. Current location: {bot.driver.current_url}", flush=True)

    except Exception as e:
        print(f"\n[ERROR] Login flow failed: {e}", flush=True)
    finally:
        bot.close()

if __name__ == "__main__":
    automated_linkedin_login()