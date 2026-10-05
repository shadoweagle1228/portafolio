FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml .
COPY src src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
COPY --from=build /install /usr/local
USER 10001
EXPOSE 8080
ENTRYPOINT ["python", "-m", "uvicorn", "auditor.main:app", "--host", "0.0.0.0", "--port", "8080"]
