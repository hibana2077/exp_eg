FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

RUN apt update && apt install -y python3 python3-pip curl wget iputils-ping

RUN pip3 install --upgrade pip

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install docling

RUN uv pip install --system --no-cache-dir -r /app/requirements.txt

RUN apt-get install tesseract-ocr libtesseract-dev libleptonica-dev pkg-config -y

COPY ../core /app

EXPOSE 14514

CMD ["python3", "main.py"]