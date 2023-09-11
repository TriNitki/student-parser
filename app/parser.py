import csv
from typing import Dict, List
from threading import Thread
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import json

class Student:
    def __init__(self, surname: str, name: str, group: str) -> None:
        self.surname = surname
        self.name = name
        self.group = group
    
    def __str__(self) -> str:
        return f'{self.surname} {self.name} {self.group}'

class NoSuchStudentException(Exception):
    def __init__(self, message="Student does not exist or has been expelled"):
        self.message = message
        super().__init__(self.message)

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
    
    def run(self) -> None:
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
    
    def parse_student(self, student: Student) -> None:
        def get_avg_grade():
            try:
                avg_grade = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div/div/span/div/ui-view/div/div[2]/div[3]/h4/span').text
            except NoSuchElementException:
                driver.close()
                raise NoSuchStudentException
            return avg_grade
        
        def get_skips_amount():
            raw_skips = driver.find_element(By.XPATH, r'/html/body/div[1]/div[4]/div[4]/table/tbody')
            skips_amount = len(raw_skips.text.splitlines())
            return skips_amount
        
        def get_skips_fraction():
            raw_lines = driver.find_elements(By.XPATH, r'//*[@id="highcharts-4"]//*[name()="svg"]/*[name()="g"][2]/*[name()="path"]')
            lines_values = [float(item.get_attribute("d").split(" ")[1]) for item in raw_lines]
            difference = max(lines_values) - min(lines_values)
            
            raw_rests = driver.find_elements(By.XPATH, r'//*[@id="highcharts-4"]//*[name()="svg"]/*[name()="g"][5]/*[name()="g"][1]/*[name()="rect"]')
            rects_heights = [float(item.get_attribute("height")) for item in raw_rests]
            
            skips_fraction = [height/difference for height in rects_heights]
            mean_skips_fraction = sum(skips_fraction) / len(skips_fraction)
            return mean_skips_fraction
        
        START_DATE  = "01-09-2022"
        END_DATE    = "01-09-2023"
        
        grade_url           = rf'https://ocenka.tusur.ru/student_search?utf8=%E2%9C%93&surname={student.surname}&name={student.name}&group={student.group}&commit=%D0%9D%D0%B0%D0%B9%D1%82%D0%B8'
        pre_attendance_url  = fr'https://attendance.tusur.ru/search?utf8=%E2%9C%93&q={student.surname}+{student.name}+{student.group}&commit=%D0%9D%D0%B0%D0%B9%D1%82%D0%B8'
        
        driver = webdriver.Chrome(
            service=self.driver_service,
            options=self.driver_options
        )
        
        # Get grade
        driver.get(grade_url)
        
        avg_grade = None
        while not avg_grade:
            avg_grade = get_avg_grade()
            
        # Get attendance
        driver.get(pre_attendance_url)
        
        post_attendance_url = driver.current_url + fr"?filter%5Bfrom%5D={START_DATE}&filter%5Bto%5D={END_DATE}"
        driver.get(post_attendance_url)
        
        skips_amount    = get_skips_amount()
        skips_fraction  = get_skips_fraction()
        
        driver.close()
        
        _save_student_csv(self.csv_path, str(student), skips_fraction, skips_amount, avg_grade)
    
    def _get_students(self) -> List[Student]:
        with open(self.students_path, "r", encoding='utf8') as f:
            students = json.load(f)
            
        if self.ignore_parsed_students:
            students = _remove_parsed_students(students)
        
        students = [
            Student(student["surname"], student["name"], student["group"]) 
            for student in students
        ]
        
        return students
    
def _remove_parsed_students(students: List[Dict[str, str]]) -> List[Dict[str, str]]:
    unparsed = []
    for student in students:
        if student["is_parsed"]:
            continue
        unparsed.append(student)
    
    return unparsed

def _save_student_csv(csv_path, name, skips_fraction, skips_amount, avg_grade) -> None:
    try:
        with open(csv_path, 'a', encoding='utf8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["name", "mean_fraction", "skips_amount", "avg_grade"])
            writer.writerow({"name": name, "mean_fraction": skips_fraction, "skips_amount": skips_amount, "avg_grade": avg_grade})
    except IOError:
        print("I/O error")