# Use the latest Python image.
FROM python:3.9

# Set environment variables for Streamlit
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Update the system and install basic dependencies
RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install -U pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Include any additional assets like images
COPY img/ /app/img/

# Expose port 8501 for Streamlit
EXPOSE 8501

# The command to run the application
CMD ["streamlit", "run", "main.py"]
