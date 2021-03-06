FROM python:3
RUN pip install flask
RUN pip install requests
RUN pip install pymongo
RUN pip install dnspython
COPY ./students_data.json /app/students_data.json
COPY ./sections.json /app/sections.json
COPY ./students_registration.json /app/students_registration.json
COPY . /app
COPY ./loadbalancer.py /app/loadbalancer.py
RUN export FLASK_ENV=development
CMD ["python", "/app/loadbalancer.py"]  