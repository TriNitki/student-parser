from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from threading import Thread, Barrier

from app.parser import parse_skips, parse_grade



STUDENT_INFO = {
    "name": "Данил",
    "surname": "Афанасьев",
    "group": "432-1"
}
"Афанасьев Данил 432-1"


options = Options()
options.add_argument("--headless")
service = Service(ChromeDriverManager().install())

driver = webdriver.Chrome(
    service=service,
    options=options
)


result = parse_skips(driver, STUDENT_INFO)
result = parse_grade(driver, STUDENT_INFO)

time.sleep(5)