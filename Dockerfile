FROM postgres:15

# Install awscli from Debian repos (no pip, no PEP 668 issue)
RUN apt-get update && apt-get install -y awscli && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["sh", "-c"]
