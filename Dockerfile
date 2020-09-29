FROM python:3.7-slim-buster
RUN apt-get update && apt-get install -y git
#TODO
RUN git clone https://github.com/obrigg/cisco-dnac-port-assignment.git
WORKDIR /cisco-dnac-port-assignment/
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "run.py"]
