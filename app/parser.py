from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import csv
from typing import Dict, List
from threading import Thread

# class EmptyStundentsError(Exception):
#     def __init__(self, message, errors):            
#         # Call the base class constructor with the parameters it needs
#         super().__init__(message)
            
#         # Now for your custom code...
#         self.errors = errors

class StudentParser:
    def __init__(
        self, 
        students_path: str,
        csv_path: str,
        number_of_threads: int = 1,
        driver_options: Options = Options(),
        driver_service: Service = Service(),
        ignore_parsed_students: bool = True
    ) -> None:
        self.students_path = students_path
        self.csv_path = csv_path
        self.number_of_threads = number_of_threads
        self.driver_options = driver_options
        self.driver_service = driver_service
        self.ignore_parsed_students = ignore_parsed_students
        self.students = self._get_students()
    
    def run(self):
        number_of_unparsed_students = len(self.students)
        for i in range(0, number_of_unparsed_students, self.number_of_threads):
            threads = []
            if (i + self.number_of_threads + 1 > number_of_unparsed_students) and (number_of_unparsed_students % self.number_of_threads != 0):
                self.number_of_threads = number_of_unparsed_students % self.number_of_threads

            for j in range(self.number_of_threads):
                t1 = Thread(target=self.parse_student, args=(self.students[j+i],)) 
                t1.start()
                threads.append(t1)

            for t in threads:
                t.join()
    
    def _get_students(self):
        import json 
        with open(self.students_path, "r", encoding='utf8') as f:
            students = json.load(f)
            
        if self.ignore_parsed_students:
            students = self._remove_parsed_students(students)
        return students
    
    def _remove_parsed_students(self, students: List[Dict[str, str]]):
        unparsed = []
        for student in students:
            if student["is_parsed"]:
                continue
            unparsed.append(student)
        
        return unparsed
    
    def _save_student_csv(self, name, mean_fraction, skips_amount, avg_grade):
        try:
            with open(self.csv_path, 'a', encoding='utf8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["name", "mean_fraction", "skips_amount", "avg_grade"])
                writer.writerow({"name": name, "mean_fraction": mean_fraction, "skips_amount": skips_amount, "avg_grade": avg_grade})
        except IOError:
            print("I/O error")
    
    
    def parse_student(self, student: Dict[str, str]):
        START_DATE = "01-09-2022"
        END_DATE = "01-09-2023"
        
        driver = webdriver.Chrome(
            service=self.driver_service,
            options=self.driver_options
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
                    driver.close()
                    return
                except NoSuchElementException:
                    continue
        
        # Get attendance
        
        driver.get(fr'https://attendance.tusur.ru/search?utf8=%E2%9C%93&q={student["surname"]}+{student["name"]}+{student["group"]}&commit=%D0%9D%D0%B0%D0%B9%D1%82%D0%B8')
        driver.get(driver.current_url + fr"?filter%5Bfrom%5D={START_DATE}&filter%5Bto%5D={END_DATE}")
        
        student_str = f'{student["surname"]} {student["name"]} {student["group"]}'
        
        skips_a = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div[4]/table/tbody')
        skips_amount = len(skips_a.text.splitlines())
        
        lines = driver.find_elements(By.XPATH, r'//*[@id="highcharts-4"]//*[name()="svg"]/*[name()="g"][2]/*[name()="path"]')
        
        lines_values = [float(item.get_attribute("d").split(" ")[1]) for item in lines]
        max_value = max(lines_values)
        min_value = min(lines_values)
        difference = max_value - min_value
        
        rects = driver.find_elements(By.XPATH, r'//*[@id="highcharts-4"]//*[name()="svg"]/*[name()="g"][5]/*[name()="g"][1]/*[name()="rect"]')
        
        rects_heights = [float(item.get_attribute("height")) for item in rects]
        
        driver.close()
        
        skips_frac = [height/difference for height in rects_heights]
        mean_skips_frac = sum(skips_frac) / len(skips_frac)
        self._save_student_csv(student_str, mean_skips_frac, skips_amount, avg_grade)
        
        
        