import re
import time


class ProgressMessage:
    def __init__(self, message):
        self.message = message
        self.last_text = None
        self.last_edit = 0
        self.last_percent = {}

    async def set(self, text, force=False):
        now = time.monotonic()
        if not force and text == self.last_text:
            return
        if not force and now - self.last_edit < 2:
            return
        self.last_text = text
        self.last_edit = now
        await self.message.edit(content=text)

    async def percent(self, label, percent, force=False):
        percent = max(0, min(100, int(percent)))
        last = self.last_percent.get(label)
        if not force and last is not None and percent - last < 5 and percent < 100:
            return
        self.last_percent[label] = percent
        await self.set(f"{label}: {percent}%", force=force or percent >= 100)


def extract_percent(text):
    matches = re.findall(r"(\d{1,3})\s*%", text)
    if not matches:
        return None
    return max(0, min(100, int(matches[-1])))
