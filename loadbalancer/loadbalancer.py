import os
import sys
import random
from flask import *
import requests
from server import Server
from pymongo import *
import json
import time
db_connected = False
db_client = None
db_cbcs = None
students_info = None
students_registration = None
sections=None
app = Flask(__name__)
algorithm_used='port_hashing'
entries=[]
server_stats=[0.0,0.0,0.0]
def connect_to_database():
    try:
        global db_client
        global db_connected
        db_client =MongoClient("mongodb+srv://sskdrn:sakthi19@cbcs.iiwws.mongodb.net/info?retryWrites=true&w=majority")
        #db_client = MongoClient('172.16.238.14',27107)
        db_connected = True
        print("Successfully connected to database")
    except Exception as e:
        print(str(e))


def seed_data():
    try:
        global db_cbcs
        global students_info
        global students_registration
        global sections
        db_cbcs = db_client.cbcs
        students_registration = db_cbcs['registration']
        students_info = db_cbcs['info']
        sections=db_cbcs['sections']
        if 'registration' in db_cbcs.list_collection_names():
            students_registration.delete_many({})
        if 'info' in db_cbcs.list_collection_names():
            students_info.delete_many({})
        if 'sections' in db_cbcs.list_collection_names():
            sections.delete_many({})
        with open('/app/students_data.json', 'r') as students_info_json:
            data = json.load(students_info_json)
            details = data['StudentsData']
            insert_ids = students_info.insert_many(details)
        with open('/app/students_registration.json', 'r') as students_reg_json:
            data = json.load(students_reg_json)
            details = data['RegistrationDetails']
            insert_ids = students_registration.insert_many(details)
        with open('/app/sections.json', 'r') as students_reg_json:
            data = json.load(students_reg_json)
            details = data['Sections']
            insert_ids = sections.insert_many(details)
        print('Data Successfully Seeded!!')
    except Exception as e:
        print("Seed Exception:",str(e))


# print('Please wait for 120 seconds to initialize database' ,file=sys.stdout)
# time.sleep(120)
connect_to_database()
seed_data()

servers=[Server('172.16.238.11',7000),Server('172.16.238.12',7000),Server('172.16.238.13',7000)]
hosts=["http://172.16.238.11:7000","http://172.16.238.12:7000","http://172.16.238.13:7000"]
ports=['7000','7001','7002']
app = Flask(__name__)
received_requests=[]
i=0
def port_hashing(port):
    global i
    i+=1
    return port%3

def least_cpu_usage():
    global server_stats
    min_cpu_usage=min(server_stats)
    try:
        server_no=server_stats.index(min_cpu_usage)
    except:
        server_no=0
    # global i
    # j=i
    # i+=1
    return server_no

@app.route('/register', methods=['POST'])
def register_directly():
    try:
      global i
      global received_requests
      global algorithm_used
      request_object = request.get_json(force=True)
      client_port=request.environ.get('REMOTE_PORT') #Client port
      server_no=port_hashing(client_port) if algorithm_used=='port_hashing' else least_cpu_usage()
      entries.append({"request": i,"host":request.remote_addr, "client_port":client_port,"server":server_no+1})
      res=requests.post(servers[server_no].url+'/register',json=request_object).json()
      res['Server']=i
      return jsonify(res)
    except Exception as e:
      return str(e)
@app.route('/changemode',methods=['POST'])
def change_mode():
    global algorithm_used
    try:
        algorithm_used = 'least_cpu_usage' if algorithm_used=='port_hashing' else 'port_hashing'
        return jsonify({"AlgorithmInUse":"PortHashing" if algorithm_used=='port_hashing' else 'LeastCPUUsage', "SwitchSuccess":True})
    except:
        return jsonify({"AlgorithmInUse":"PortHashing" if algorithm_used=='port_hashing' else 'LeastCPUUsage', "SwitchSuccess":False})

@app.route('/dashboard')
def dashboard():
    global algorithm_used
    server1_info=requests.post(hosts[0]+'/getsysteminfo').json()
    server2_info=requests.post(hosts[1]+'/getsysteminfo').json()
    server3_info=requests.post(hosts[2]+'/getsysteminfo').json()
    print(server1_info,file=sys.stdout)
    return render_template('dashboard.j2',entries=entries, server1_info=server1_info,server2_info=server2_info,server3_info=server3_info,algorithm_used=algorithm_used)
@app.route('/getsystemstats')
def get_system_stats():
    global server_stats
    server1_info=requests.post(hosts[0]+'/getsysteminfo').json()
    server2_info=requests.post(hosts[1]+'/getsysteminfo').json()
    server3_info=requests.post(hosts[2]+'/getsysteminfo').json()
    server_stats=[server1_info['cpu_usage'],server2_info['cpu_usage'],server3_info['cpu_usage']]
    return jsonify({"server1_info":server1_info,"server2_info":server2_info,"server3_info":server3_info})
@app.route('/')
def handle_requests():
#    try:
      global i
      global received_requests
      global algorithm_used
      global entries
      global ports
      client_port=request.environ.get('REMOTE_PORT') #Client port
      server_no=port_hashing(client_port) if algorithm_used=='port_hashing' else least_cpu_usage()
      entries.append({"request": i,"host":request.remote_addr, "client_port":client_port,"server":server_no+1})
      print('Redirect to http://localhost:'+ports[server_no]+'/login',file=sys.stdout)
      return redirect('http://localhost:'+ports[server_no]+'/login')
#    except Exception as e:
    #   return str(e)


    

if __name__ == '__main__':
   app.run(host="0.0.0.0", port=8000, debug=True)