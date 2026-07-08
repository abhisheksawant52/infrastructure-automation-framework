# syntax=docker/dockerfile:1

# ---- builder: build a wheel for the iac_framework package ----
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml requirements.txt ./
COPY src ./src

RUN python -m pip install --upgrade pip build && \
    python -m build --wheel

# ---- runtime: install the wheel into a slim, non-root image ----
FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 iac && \
    useradd --uid 1000 --gid iac --create-home --shell /usr/sbin/nologin iac

WORKDIR /home/iac/app

COPY --from=builder /build/dist/*.whl /tmp/
RUN python -m pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

USER iac

ENTRYPOINT ["iac"]
CMD ["--help"]
