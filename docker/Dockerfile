# AI FinOps Platform — Lambda container image
# Used for local development and Trivy security scanning

FROM public.ecr.aws/lambda/python:3.11

# Copy Lambda source
COPY lambda/src/ ${LAMBDA_TASK_ROOT}/
COPY lambda/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default handler
CMD ["collector.lambda_handler"]
