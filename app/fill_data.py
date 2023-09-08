import json 

try:
    with open("students.json", "r", encoding='utf8') as f:
        students = json.load(f)
except:
    students = []

while True:
    a = input()
    if a == "e":
        break
    if "Студент" in a:
        parsed_student = a.replace("\\t", " ").replace(".", "").split( )
        surname = parsed_student[0]
        name = parsed_student[1]
        group = parsed_student[6]
        
        if name[0] == surname[0] and surname[1] == surname[2]:
            surname = surname[2:]
        
        student_dict = {
            "surname": surname,
            "name": name,
            "group": group,
            "is_parsed": False
        }
        
        if student_dict not in students:
            students.append(student_dict)
        
        

with open("students.json", "w", encoding='utf8') as f:
    f.write(json.dumps(students, indent=4, ensure_ascii=False))
        