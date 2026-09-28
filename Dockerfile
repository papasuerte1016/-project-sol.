FROM python:3.12-slim
WORKDIR /app
COPY sol_ai_v0_4.py /app/sol_ai_v0_4.py
COPY sol_compute_token.py /app/sol_compute_token.py
COPY sol_model_adapter.py /app/sol_model_adapter.py
ENV PYTHONUNBUFFERED=1
CMD ["python", "/app/sol_ai_v0_4.py", "chat", "Project Sol first Railway model-backed run"]
