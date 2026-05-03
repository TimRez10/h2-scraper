FROM python:3.11.12

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install
RUN playwright install-deps

COPY . .

CMD ["python", "./main.py"]
