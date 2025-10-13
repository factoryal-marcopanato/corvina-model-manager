FROM python:3.12.12-alpine3.22

RUN mkdir /app
WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY src/ src

# Generate *.pyc files
RUN python -m compileall -o 2 -f -j 0 /app/

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY CHANGELOG.txt CHANGELOG.txt

ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
CMD ["python", "src/corvina_model_manager.py"]
