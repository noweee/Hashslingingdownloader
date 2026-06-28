# Hash Slinging Server Control

Use `serverctl.sh` from the bot folder on Ubuntu:

```bash
cd /srv/server/bot
chmod +x serverctl.sh
```

## Easy Commands

Start both:

```bash
./serverctl.sh up
```

Restart both:

```bash
./serverctl.sh reboot
```

Stop both:

```bash
./serverctl.sh down
```

Check both:

```bash
./serverctl.sh status
```

## Individual Commands

Start only the bot:

```bash
./serverctl.sh start bot
```

Restart only the bot:

```bash
./serverctl.sh restart bot
```

Stop only the bot:

```bash
./serverctl.sh stop bot
```

Start only Minecraft:

```bash
./serverctl.sh start mc
```

Restart only Minecraft:

```bash
./serverctl.sh restart mc
```

Stop only Minecraft:

```bash
./serverctl.sh stop mc
```

## What It Uses

The script uses these folders:

```text
/srv/server/bot
/srv/server/minecraft
```

It runs both inside `screen` so they keep running after you log out.

The screen names are:

```text
hsd-bot
hsd-mc
```

To open one manually:

```bash
screen -r hsd-bot
screen -r hsd-mc
```

Detach from a screen:

```text
Ctrl+A, then D
```
