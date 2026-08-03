FROM python:3.11-slim

# System dependencies for WeasyPrint + lxml + Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint dependencies
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libgdk-pixbuf2.0-0 \
    # lxml
    libxml2 \
    libxslt1.1 \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (for SVG chart capture)
RUN playwright install chromium --with-deps

# Copy application code
COPY . .

# Create output directory for generated PDFs
RUN mkdir -p /app/outputs

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
