FROM python
COPY . .
CMD ["python", "main.py"]
RUN pip install pymongo && pip install bcrypt
EXPOSE 8080