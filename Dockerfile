FROM python:3.10-slim
WORKDIR /app
COPY wheels/ ./wheels/
RUN pip install ./wheels/PyMuPDF-1.23.7-*.whl
COPY . .
CMD ["python", "round1b/analyzer.py"]
