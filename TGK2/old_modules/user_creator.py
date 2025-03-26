import json
import time
import os
import asyncio
from random import randint
from pprint import pprint

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from modules import settings
from modules import proxy
from modules import numberphones


def text_check(test: str, driver) -> bool:
    if test in driver.page_source:
        print(driver.page_source)
        return True
    return False


def main():
    options = Options()

    service = FirefoxService(executable_path=settings.GECKO_DRIVER_PATH)
    
    driver = webdriver.Firefox(service=service, options=options)

    driver.get("https://web.telegram.org/")

    time.sleep(20)

    print('Selenium start')

    try:
        login_button = driver.find_element(By.TAG_NAME, 'button')
        
        time.sleep(randint(1, 5))

        login_button.click()

    except Exception as e:
        print(f"Ошибка: {e}")
        
    actions = ActionChains(driver)



    proxy_country = asyncio.run(proxy.get_country())
    print(proxy_country)

    # while True:
    #     for country in proxy_country:
    #         response = asyncio.run(numberphones.get_numberphone(country))
    #         if response != 'NO_NUMBERS':
    #             if 'ACCESS_NUMBER' in response:
    #                 numberphone_id, numberphone = response.split(':')[1::]
                
    #                 print(country)
    #                 print(numberphone_id, numberphone)
    #             else:
    #                 print(response)
    #                 quit()
    #             break
            
    #     response = asyncio.run(numberphones.set_status(id=numberphone_id, status=1))
    #     pprint(response)
    if True:
        

        # phone-edit
        print('Numberphone error, use test')
        for _ in range(15):
            actions.send_keys(Keys.BACKSPACE).perform()
            time.sleep(1 - randint(1, 9) / 10)
        

        text = ...
        for char in text:
            actions.send_keys(char).perform()
            time.sleep(1 - randint(1, 9) / 10)

        actions.send_keys(Keys.ENTER).perform()

        time.sleep(randint(5, 10))



        # if input('ЗБС?') == 'YES':
        #     while input('ЕБАШИТЬ???'):
        #         response = asyncio.run(numberphones.get_code(id=numberphone_id))
        #         pprint(response)

        #     if input('ЗБС?') == 'YES':
        #         response = asyncio.run(numberphones.set_status(id=numberphone_id, status=6))
        #         pprint(response)
        #         break

        # else:
        #     response = asyncio.run(numberphones.set_status(id=numberphone_id, status=-1))
        #     pprint(response)
            
        #     if not text_check('Please confirm your country code and enter your phone number.', driver=driver):
        #         try:
        #             return_button = driver.find_element(By.CLASS_NAME, 'phone-edit')
                
        #             time.sleep(randint(1, 5))

        #             return_button.click()
        #         except Exception:
        #             print('G')



    
    
    input(' >>> ')

    driver.quit()

    return 'Selenium has completed its work'


async def init_creator():
    loop = asyncio.get_running_loop()
    process_result = await loop.run_in_executor(None, main)
    return process_result


if __name__ == "__main__":
    main()
