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
mkdir -p ~/minecraft-server
cd ~/minecraft-server
```

## 3. Download Paper

Download the Paper server jar from:

```text
https://papermc.io/downloads/paper
```

Put it in:

```text
~/minecraft-server/paper.jar
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
cd "$HOME/minecraft-server"
java -Xms1G -Xmx4G -jar paper.jar nogui
```

Save it, then run:

```bash
chmod +x start.sh
```

## 6. Start The Server

```bash
cd ~/minecraft-server
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

## 7. Configure The Discord Bot Check

In the bot's `.env` file on the same Ubuntu server:

```env
MINECRAFT_HOST=127.0.0.1
MINECRAFT_PORT=25565
MINECRAFT_NAME=SBPH Minecraft
MINECRAFT_STATUS_INTERVAL=60
```

Restart the Discord bot after editing `.env`.

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
