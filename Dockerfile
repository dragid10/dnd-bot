FROM python:3.10.5
RUN pip install pipenv
RUN ls -hal
COPY . /dnd-bot
COPY .git /dnd-bot/.
WORKDIR /dnd-bot
RUN pipenv install --deploy
CMD [ "pipenv", "run", "python3", "bot.py" ]