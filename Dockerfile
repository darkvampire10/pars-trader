FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN useradd --uid 10001 --create-home appuser && mkdir /app/data && chown appuser:appuser /app/data
COPY --chown=appuser:appuser pars_trader /app/pars_trader
USER appuser
CMD ["python", "-m", "pars_trader", "run"]
