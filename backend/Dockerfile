FROM registry.access.redhat.com/ubi9/python-312

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/uploads && chgrp -R 0 /data && chmod -R g+rwx /data

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 5001

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:5001", "app:app"]
