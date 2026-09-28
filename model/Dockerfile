FROM ollama/ollama:latest
ENV OLLAMA_HOST=http://0.0.0.0:11434
EXPOSE 11434
ENTRYPOINT ["/bin/sh","-c"]
CMD ["export OLLAMA_HOST=http://0.0.0.0:11434; echo \"SOL_MODEL_EFFECTIVE_HOST=$OLLAMA_HOST\"; exec ollama serve"]
