import os
import sys
from flask import *
import socket
import time
import psutil
from pymongo import *
db_connected = False
db_client=None
db_cbcs = None
students_info = None
sections=None
students_registration = None
port = 7000
server = os.getenv('APP')
app = Flask(__name__)
server_title=''

def connect_to_database():
    try:
        global db_cbcs
        global students_info
        global students_registration
        global sections
        db_client = MongoClient("mongodb+srv://<username>:<password>@<db>.iiwws.mongodb.net/info?retryWrites=true&w=majority")
        # db_client = MongoClient('172.16.238.14',27107)
        db_connected = True
        db_cbcs = db_client.cbcs
        students_registration = db_cbcs['registration']
        students_info = db_cbcs['info']
        sections=db_cbcs['sections']
        print("Successfully connected to database")
    except Exception as e:
        print(str(e))
print('Please wait for 150 seconds to initialize database' ,file=sys.stdout)
time.sleep(150)
connect_to_database()

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.j2', server_title=server_title, error=request.args.get('error'))


@app.route('/login', methods=['POST'])
def login():
    global server_title
    global db_cbcs
    global students_info
    global students_registration
    global sections
    reg_no = request.form.get('regno')
    if reg_no == '':
        return redirect(url_for('login', error='invalid'))
    else:
        reg_no = int(reg_no)
        entry = students_registration.find_one({"RegisterNumber": reg_no})
        if entry == None:
            return redirect(url_for('login', error='invalid'))
        else:
            if entry['Registered']:
                return redirect(url_for('regdetails', reg_no=reg_no))
            else:
                return redirect(url_for('selection_screen', reg_no=reg_no, error='selection'))


@app.route('/select/<reg_no>/<error>', methods=['GET'])
def selection_screen(reg_no, error):
    global db_cbcs
    global students_info
    global students_registration
    global sections
    reg_no = int(reg_no)
    student_details = students_info.find_one({"RegisterNumber": reg_no})
    section_details = []
    for entry in sections.find():
        section_details.append(entry)
    return render_template('selection.j2', student_details=student_details, section_details=section_details, error=error, server_title=server_title)


@app.route('/select', methods=['POST'])
def confirm_select():
    global db_cbcs
    global students_info
    global students_registration
    global sections
    preferred_section = request.form['section']
    reg_no = int(request.form.get('regno'))
    section_details = sections.find_one({"Section": preferred_section})
    student_details = students_info.find_one({'RegisterNumber': reg_no})
    current_intake = section_details['CurrentIntake']
    max_intake = section_details['MaxIntake']
    if(current_intake < max_intake):
        section_updated_entry = sections.find_one_and_update({"Section": preferred_section}, {
                                                             '$inc': {'CurrentIntake': 1}}, return_document=ReturnDocument.AFTER)
        print(section_updated_entry, file=sys.stdout)
        students_registration.find_one_and_update({"RegisterNumber": reg_no}, {
                                                  '$set': {'Registered': True, 'AllottedSection': preferred_section}})
        return redirect(url_for('regdetails', reg_no=reg_no))
    else:
        return redirect(url_for('selection_screen', reg_no=reg_no, error='unavailable'))


@app.route('/regdetails/<reg_no>', methods=['GET'])
def regdetails(reg_no):
    global db_cbcs
    global students_info
    global students_registration
    global sections
    student_details = students_info.find_one({'RegisterNumber': int(reg_no)})
    print(student_details, file=sys.stdout)
    registration_details = students_registration.find_one(
        {'RegisterNumber': int(reg_no)})
    print(registration_details, file=sys.stdout)
    return render_template('regdetails.j2', student_details=student_details, registration_details=registration_details)


@app.route('/register', methods=['POST'])
def reg_direct():
    global db_cbcs
    global students_info
    global students_registration
    global sections
    res = {}
    # try:
    request_object = request.get_json(force=True)
    preferred_section = request_object['PreferredSection']
    reg_no = int(request_object['RegisterNumber'])
    section_details = sections.find_one({"Section": preferred_section})
    student_details = students_info.find_one({'RegisterNumber': reg_no})
    students_registration_details = students_registration.find_one(
        {'RegisterNumber': reg_no})
    if section_details == None or section_details == {}:
        res['ErrorCode'] = 2
        res['ErrorMessage'] = 'Section does not exist.'
    elif student_details == None or student_details == {}:
        res['ErrorCode'] = 1
        res['ErrorMessage'] = 'Invalid Register Number'
    elif students_registration_details['AllottedSection'] != None:
        res['ErrorCode'] = 3
        res['ErrorMessage'] = 'Student already registered'
        res['AllottedSection'] = students_registration_details['AllottedSection']
    else:
        current_intake = section_details['CurrentIntake']
        max_intake = section_details['MaxIntake']
        if(current_intake < max_intake):
            section_updated_entry = sections.find_one_and_update({"Section": preferred_section}, {
                                                                '$inc': {'CurrentIntake': 1}}, return_document=ReturnDocument.AFTER)
            print(section_updated_entry, file=sys.stdout)
            students_registration.find_one_and_update({"RegisterNumber": reg_no}, {
                                                    '$set': {'Registered': True, 'AllottedSection': preferred_section}})
            res['ErrorCode'] = 0
            res['ErrorMessage'] = 'Registration successfull.'
            res['AllottedSection'] = preferred_section
        else:
            res['ErrorCode'] = 4
            res['ErrorMessage'] = 'Section unavailable.'
    # except Exception as e:
    #     res['ErrorCode'] = 5
    #     res['ErrorMessage'] = 'Error occured while handling the request.'
    #     res['Exception']= str(e)
    return jsonify(res)

@app.route('/getsysteminfo',methods=['POST'])
def get_system_info():
    stats={}
    stats['server']=server
    stats['cpu_usage']=psutil.cpu_percent()
    stats['memory_usage']=psutil.virtual_memory()[2]
    return jsonify(stats)

@app.route('/')
def sample():
    return f'{os.environ["APP"]}'


if __name__ == '__main__':
    port = 7000
    if server=='server-1':
       server_title='Server 1'
    elif server=='server-2':
       server_title='Server 2'
    else:
       server_title='Server 3'
    app.run(host='0.0.0.0', port=port, debug=True)
    print("Server: ", server,file=sys.stdout)
    print("IP Address: ", socket.gethostbyname(socket.gethostname()),file=sys.stdout)
    print("Port: ", port,file=sys.stdout)
    
