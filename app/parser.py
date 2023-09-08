from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from threading import Barrier
import time
import csv

from typing import Dict, List

from config import config

def __timer(func):
    def wrapper_func(barrier, service, options, STUDENT_INFO):
        before = time.time()
        func(barrier, service, options, STUDENT_INFO)
        after = time.time()
        print(f"time: {after - before }")
    return wrapper_func

@__timer
def parse_grade(barrier: Barrier, service: Service, options: Options, student: Dict[str, str]):
    driver = webdriver.Chrome(
        service=service,
        options=options
    )

    driver.get(
        rf'https://ocenka.tusur.ru/student_search?utf8=%E2%9C%93&surname={student["surname"]}&name={student["name"]}&group={student["group"]}&commit=%D0%9D%D0%B0%D0%B9%D1%82%D0%B8'
    )
    
    avg_grade = None
    not_found = None
    
    while not avg_grade and not not_found:
        try:
            avg_grade = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div/div/span/div/ui-view/div/div[2]/div[3]/h4/span').text
        except NoSuchElementException:
            try:
                not_found = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div/div[2]/p[1]').text
            except NoSuchElementException:
                continue
    
    student_str = f'{student["surname"]} {student["name"]} {student["group"]}'

    if not_found:
        print(f"{student_str}: NOT FOUND!")
        return

    print(f"{student_str}: avg_grade = {avg_grade}")
    
    # Get attendance
    
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
    
    try:
        with open("prikol.csv", 'a', encoding='utf8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["name", "mean_fraction", "skips_amount", "avg_grade"])
            writer.writerow({"name": student_str, "mean_fraction": mean_skips_frac, "skips_amount": skips_amount, "avg_grade": avg_grade})
    except IOError:
        print("I/O error")

def remove_parsed_students(students: List[Dict[str, str]]):
    unparsed = []
    for student in students:
        if student["is_parsed"]:
            continue
        unparsed.append(student)
    
    return unparsed