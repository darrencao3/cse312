FROM python
COPY . .
CMD ["python", "main.py"]
RUN pip install pymongo
EXPOSE 8080