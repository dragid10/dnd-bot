FROM python:3.12

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /dnd-bot
WORKDIR /dnd-bot

# Install dependencies using uv (syncs from uv.lock)
RUN uv sync --frozen

CMD [ "uv", "run", "python3", "-m", "bot"]
