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

# Install python dependencies directly
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run the cli tool automatically
CMD ["python3", "src/main.py"]
