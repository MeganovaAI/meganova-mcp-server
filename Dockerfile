FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

ENV TRANSPORT=http
ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

CMD ["meganova-mcp-server"]
