# Ubuntu Minecraft Server Setup

This is the Minecraft side of the setup. Run these steps on the Ubuntu server, not in the Discord bot folder.

The Discord bot only checks whether this Minecraft server is reachable and shows the Ubuntu machine's power-on time.

## 1. Install Java

On the Ubuntu server:

```bash
sudo apt update
sudo apt install -y openjdk-21-jre-headless curl screen
java -version
```

You want Java version `21`.

## 2. Create A Server Folder

```bash
sudo mkdir -p /srv/server/minecraft
sudo chown -R $USER:$USER /srv/server/minecraft
cd /srv/server/minecraft
```

## 3. Download Paper

Download the Paper server jar from:

```text
https://papermc.io/downloads/paper
```

Put it in:

```text
/srv/server/minecraft/paper.jar
```

## 4. Accept The EULA

Only do this if you accept Minecraft's EULA:

```bash
echo "eula=true" > eula.txt
```

## 5. Create A Start Script

```bash
nano start.sh
```

Paste:

```bash
#!/usr/bin/env bash
cd /srv/server/minecraft
java -Xms1G -Xmx4G -jar paper.jar nogui
```

Save it, then run:

```bash
chmod +x start.sh
```

## 6. Start The Server

```bash
cd /srv/server/minecraft
screen -S minecraft ./start.sh
```

Wait until the console says `Done`.

Detach from the server console:

```text
Ctrl+A, then D
```

Return to the server console later:

```bash
screen -r minecraft
```

Stop the server safely from inside the console:

```text
stop
```

## 7. Create The Discord Status Config

Keep the Minecraft status settings in the Minecraft folder:

```bash
nano /srv/server/minecraft/discord-status.json
```

Paste:

```json
{
  "host": "127.0.0.1",
  "port": 25565,
  "name": "Hash Slinging Server",
  "status_interval": 60
}
```

The Discord bot reads this file from `/srv/server/minecraft`, so the Minecraft-specific settings stay with the Minecraft server.

If you ever move this file somewhere else, set this one bot `.env` value:

```env
MINECRAFT_STATUS_CONFIG=/srv/server/minecraft/discord-status.json
```

Otherwise, you do not need to add Minecraft host, port, or name to the bot `.env`.

Restart the Discord bot after editing `discord-status.json`.

## 8. Test In Discord

In Discord, run:

```text
h!mc
```

The bot should reply with:

- whether Minecraft is online
- player count
- latency
- Minecraft version
- Ubuntu server power-on time

The bot's Discord presence will also update about once a minute with online/offline status and power-on time.
