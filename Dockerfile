# Stage 1: Build python packages
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python runtimes into wheels directory
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final runtime image
FROM python:3.12-slim

WORKDIR /app

# Install FFmpeg, ImageMagick (TextClip dependencies), and font utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    imagemagick \
    curl \
    unzip \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Download and install Montserrat font natively into OS for ImageMagick/MoviePy
RUN curl -L -O "https://github.com/JulietaUla/Montserrat/archive/refs/heads/master.zip" \
    && unzip master.zip \
    && mkdir -p /usr/share/fonts/truetype/montserrat \
    && cp Montserrat-master/fonts/ttf/*.ttf /usr/share/fonts/truetype/montserrat/ \
    && rm -rf master.zip Montserrat-master \
    && fc-cache -f -v

# Bypass strict ImageMagick policies that block TextClip generation
RUN find /etc/ImageMagick* -name "policy.xml" -exec sed -i '/<policy domain="path" rights="none" pattern="@\*"/d' {} + || true

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy project files
COPY . .

# Run the cli tool automatically
CMD ["python3", "src/main.py"]
