 docker run --init -d --name="home-assistant" -e "TZ=America/New_York" -v /home/me/dev/media_player.sony/test_config:/config --net=host homeassistant/home-assistant:stable

