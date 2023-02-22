# cardgame_bot

## Docker Bot Deployment
Deployment instructions using docker.

<h3>Prepare the local environment:</h3>
  
  - Install docker using the official manual: https://docs.docker.com/engine/install/ubuntu/ (Ubuntu server).
  
  - Clone the project to the server with git.

<h3>Create docker image</h3>

```
docker build -t cardgame_bot .
```

  - -t specifies the name.
  
  - . specifies the repo that the image is based on (project folder).



```
docker run -t -i -d --restart unless-stopped --name cardgame_bot_run cardgame_bot
```
  - -t (--tty) allocates a pseudo-TTY.
  
  - -i (--interactive) keeps STDIN open even when not attached.
  
  - -d (--detach) will run container in background and prints container ID.
  
  - --restart unless-stopped' will restart the container in any event except 'docker container stop' command.
  
  - --name name the container.
  
  - Last argument in the command is the name of the image used for container creation.
  
  
 ## 'Dockerfile' info

     FROM python:3 
     # Specifies which docker image to use as base
  
     WORKDIR /root/cardgame_bot
     # Directory of the project on the server
  
     COPY requirements.txt ./
     # Copying requirements into the image
  
     RUN pip install --no-cache-dir -r requirements.txt
     # Install project dependencies on the image without caching
  
     COPY . .
     # Copy the project in the current directory into the image
  
     CMD [ "python3", "./card_game_bot.py" ]
     # Run the app
