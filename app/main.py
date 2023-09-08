from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from threading import Thread, Barrier
import json 

from app.parser import parse_grade, remove_parsed_students

try:
    with open("students.json", "r", encoding='utf8') as f:
        students = json.load(f)
except:
    exit

unparsed_students = remove_parsed_students(students)

options = Options()
options.add_argument("--headless")
service = Service(ChromeDriverManager().install())
# service = Service()

number_of_threads = 8
number_of_unparsed_students = len(unparsed_students) + 1

barrier = Barrier(number_of_threads)

for i in range(0, number_of_unparsed_students, number_of_threads):
    threads = []
    if i + number_of_threads + 1 > number_of_unparsed_students:
        number_of_threads = number_of_unparsed_students % number_of_threads - 1

    for j in range(int(number_of_threads)):
        t1 = Thread(target=parse_grade, args=(barrier, service, options, unparsed_students[j+i],)) 
        t1.start()
        threads.append(t1)

    for t in threads:
        t.join()
