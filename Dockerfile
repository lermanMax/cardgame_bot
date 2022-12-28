FROM python:3

WORKDIR /root/cardgame_bot

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "./card_game_bot.py" ]
