FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5001
CMD ["python", "./services/products.py"]