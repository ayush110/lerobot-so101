FROM python:3.12-slim

WORKDIR /workspace
COPY pyproject.toml README.md ./

# Project-specific images should pin a lockfile and copy only their required
# packages. This base target is intentionally non-actuating.
CMD ["python", "-c", "print('SO-101 deployment image: no policy bundle selected')"]
