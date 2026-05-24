FROM debian:bookworm-slim

# Copy installation and startup scripts
COPY install.sh /app/install.sh
COPY start-xray.sh /usr/local/bin/start-xray.sh
COPY start-admin.sh /usr/local/bin/start-admin.sh
COPY mrh-admin-server.py /usr/local/bin/mrh-admin-server.py

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash git curl wget unzip tzdata openssl ca-certificates python3 \
    && rm -rf /var/lib/apt/lists/*

# Install Xray
RUN chmod +x /app/install.sh && /app/install.sh

# Set executable permissions
RUN chmod +x /usr/local/bin/start-xray.sh \
             /usr/local/bin/start-admin.sh \
             /usr/local/bin/mrh-admin-server.py

# Copy configuration and admin panel
COPY config.json /etc/config.json
COPY admin /opt/mrh-admin

# Start Xray and admin server, then tail logs
CMD ["/bin/bash", "-lc", "/usr/local/bin/start-xray.sh && /usr/local/bin/start-admin.sh && tail -f /tmp/xray.log"]
