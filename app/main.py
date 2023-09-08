from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from app.parser import StudentParser
import time

def timer(func):
    def wrapper(parser):
        before = time.time()
        func(parser)
        after = time.time()
        print(f"time: {after - before }")
    return wrapper

options = Options()
options.add_argument("--headless")
service = Service(ChromeDriverManager().install())

print("poshla ebatoriya")

Parser = StudentParser( 
    students_path=r"students.json",
    csv_path=r"students.csv",
    number_of_threads=4,
    driver_options = options,
    driver_service = service
)

@timer
def parser_and_timer(Parser):
    Parser.run()

parser_and_timer(Parser)