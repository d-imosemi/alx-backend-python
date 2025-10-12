FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /messaging_app

# Copy requirements.txt first to leverage Docker cache
COPY Requirements.txt /messaging_app/

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r Requirements.txt

# Copy the rest of the project
COPY . /messaging_app/
# Expose the port Django runs on
EXPOSE 8000

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
