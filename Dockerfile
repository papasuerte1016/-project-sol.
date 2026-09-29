FROM python:3.12-slim
WORKDIR /app
COPY sol_ai_v0_4.py /app/sol_ai_v0_4.py
COPY sol_compute_token.py /app/sol_compute_token.py
COPY sol_model_adapter.py /app/sol_model_adapter.py
COPY sol_e2e_test.py /app/sol_e2e_test.py
COPY sol_runtime.py /app/sol_runtime.py
COPY sol_external_probe.py /app/sol_external_probe.py
ENV PYTHONUNBUFFERED=1
CMD ["python", "/app/sol_runtime.py"]
