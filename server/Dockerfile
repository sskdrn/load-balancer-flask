FROM python:3
RUN pip install flask
RUN pip install pymongo
RUN pip install psutil
RUN pip install dnspython
COPY . /app
COPY ./app.py /app/app.py
CMD ["python", "/app/app.py"]