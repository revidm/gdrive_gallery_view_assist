ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk add --no-cache python3 py3-pip ca-certificates

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /app/requirements.txt

COPY app /app/app

EXPOSE 8099

ENTRYPOINT ["python3", "-m", "app.server"]
