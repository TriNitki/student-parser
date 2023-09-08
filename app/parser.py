from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
import time

from typing import Dict

from config import config

def __timer(func):
    def wrapper_func(driver, student):
        before = time.time()
        func(driver, student)
        after = time.time()
        print(f"time: {after - before }")
    return wrapper_func

@__timer
def parse_skips(driver: webdriver.Chrome, student: Dict[str, str]):
    driver.get(r'https://attendance.tusur.ru/')

    student_str = f'{student["surname"]} {student["name"]} {student["group"]}'

    student_input = driver.find_element(By.XPATH, r'//*[@id="q"]')
    student_input.send_keys(student_str)

    submit = driver.find_element(By.XPATH, r'//*[@id="search_form"]/form/div/div[2]/input')
    submit.click()

    date_picker = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div[1]/div/a[4]')
    date_picker.click()

    time.sleep(0.4)

    date_from = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div[1]/div/form/input[1]')
    ActionChains(driver).move_to_element(date_from).send_keys_to_element(date_from, config.START_DATE).perform()

    date_to = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div[1]/div/form/input[2]')
    ActionChains(driver).move_to_element(date_to).send_keys_to_element(date_to, config.END_DATE).perform()

    date_submit = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div[1]/div/form/input[3]')
    ActionChains(driver).move_to_element(date_submit).click(date_submit).perform()

    skips_a = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div[4]/table/tbody')
    skips_amount = len(skips_a.text.splitlines())
    
    lines = driver.find_elements(By.XPATH, r'//*[@id="highcharts-4"]//*[name()="svg"]/*[name()="g"][2]/*[name()="path"]')
    
    lines_values = [float(item.get_attribute("d").split(" ")[1]) for item in lines]
    max_value = max(lines_values)
    min_value = min(lines_values)
    difference = max_value - min_value
    
    rects = driver.find_elements(By.XPATH, r'//*[@id="highcharts-4"]//*[name()="svg"]/*[name()="g"][5]/*[name()="g"][1]/*[name()="rect"]')
    
    rects_heights = [float(item.get_attribute("height")) for item in rects]
    skips_frac = [height/difference for height in rects_heights]
    mean_skips_frac = sum(skips_frac) / len(skips_frac)
    
    return {"mean_fraction": mean_skips_frac, "skips_amount": skips_amount}

@__timer
def parse_grade(driver: webdriver.Chrome, student: Dict[str, str]):
    driver.get(r'https://ocenka.tusur.ru/')
    
    surname_input = driver.find_element(By.XPATH, r'//*[@id="surname"]')
    surname_input.send_keys(student["surname"])
    
    name_input = driver.find_element(By.XPATH, r'//*[@id="name"]')
    name_input.send_keys(student["name"])
    
    group_input = driver.find_element(By.XPATH, r'//*[@id="group"]')
    group_input.send_keys(student["group"])
    
    submit_input = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div/div[1]/form/div[4]/input')
    submit_input.click()
    
    avg_grade = 0
    
    while not avg_grade:
        try:
            avg_grade = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div/div/span/div/ui-view/div/div[2]/div[3]/h4/span').text
        except NoSuchElementException:
            pass
    
    return avg_grade