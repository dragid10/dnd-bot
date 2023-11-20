FROM python:3.11
RUN pip install poetry
COPY . /dnd-bot
WORKDIR /dnd-bot
RUN poetry install
CMD [ "poetry", "run", "python3", "-m", "bot"]
