FROM python:3.11-slim-buster

# Set default PUID and PGID (can be overridden by environment variables when running the container)
ENV PUID=1000
ENV PGID=1000
ENV USER_NAME=bot
ENV GROUP_NAME=bot

# Create the user and group based on the environment variables
RUN groupadd -g ${PGID} ${GROUP_NAME} && \
    useradd -u ${PUID} -g ${PGID} -m ${USER_NAME}
WORKDIR /opt/app

# Copy and install requirements first to leverage Docker cache
COPY requirements.txt /opt/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python files into the container
COPY *.py /opt/app/

# Change ownership of the files to the user and group
RUN chown -R ${USER_NAME}:${GROUP_NAME} /opt/app

# Switch to the non-root user
USER ${USER_NAME}

# Command to run the bot
CMD ["python", "bot.py"]
