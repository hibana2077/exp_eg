FROM ubuntu:22.04

RUN apt update && apt install -y python3 python3-pip curl wget iputils-ping

RUN pip3 install --upgrade pip

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN uv pip install docling --extra-index-url https://download.pytorch.org/whl/cpu

RUN uv pip install --system --no-cache-dir -r /app/requirements.txt

RUN apt-get install tesseract-ocr libtesseract-dev libleptonica-dev pkg-config -y

COPY . /app

EXPOSE 14514

CMD ["python3", "main.py"]