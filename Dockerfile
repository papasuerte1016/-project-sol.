FROM python:3.12-slim
WORKDIR /app
COPY sol_ai_v0_4.py /app/sol_ai_v0_4.py
COPY sol_compute_token.py /app/sol_compute_token.py
COPY sol_model_adapter.py /app/sol_model_adapter.py
COPY sol_e2e_test.py /app/sol_e2e_test.py
COPY sol_runtime.py /app/sol_runtime.py
COPY sol_external_probe.py /app/sol_external_probe.py
COPY sol_bridge_endpoint.py /app/sol_bridge_endpoint.py
COPY sol_native_ai.py /app/sol_native_ai.py
COPY sol_critique_wise_network.py /app/sol_critique_wise_network.py
COPY sol_predeploy_checks.py /app/sol_predeploy_checks.py
ENV PYTHONUNBUFFERED=1
CMD ["python", "/app/sol_runtime.py"]

COPY sol_teaches_wise.py /app/sol_teaches_wise.py
