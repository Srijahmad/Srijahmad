from highrise import BaseBot, Position
from highrise.models import SessionMetadata, User
from highrise import __main__
from asyncio import run as arun
import random

class Bot(BaseBot):
    dancs = ["idle-loop-sitfloor", "emote-tired", "emoji-thumbsup", "emoji-angry", "dance-macarena", "emote-hello", "dance-weird", "emote-superpose", "idle-lookup", "idle-hero", "emote-wings", "emote-laughing", "emote-kiss", "emote-wave", "emote-hearteyes", "emote-theatrical", "emote-teleporting", "emote-slap", "emote-ropepull", "emote-think", "emote-hot", "dance-shoppingcart", "emote-greedy", "emote-frustrated", "emote-float", "emote-baseball", "emote-yes", "idle_singing", "idle-floorsleeping", "idle-enthusiastic", "emote-confused", "emoji-celebrate", "emote-no", "emote-swordfight", "emote-shy", "dance-tiktok2", "emote-model", "emote-charging", "emote-snake", "dance-russian", "emote-sad", "emote-lust", "emoji-cursing", "emoji-flex", "emoji-gagging", "dance-tiktok8", "dance-blackpink", "dance-pennywise", "emote-bow", "emote-curtsy", "emote-snowball", "emote-snowangel", "emote-telekinesis", "emote-maniac", "emote-energyball", "emote-frog", "emote-cute", "dance-tiktok9", "dance-tiktok10", "emote-pose7", "emote-pose8", "idle-dance-casual", "emote-pose1", "emote-pose3", "emote-pose5", "emote-cutey","emote-Relaxing","emote-model","emote-cursty"]

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        print("hi im alive?")
        self.highrise.tg.create_task(self.highrise.teleport(
            session_metadata.user_id, Position(0, 0,0 , "FrontLeft")))

    async def on_user_join(self, user: User) -> None:
        await self.highrise.chat(f"ولكم🤍♥️رقصني-صعدني-نزلني-وقت موتي-نسبة الحب-نسبة كرهي-مصيري- طيرني-🤍♥️,  {user.username}!")

    async def on_whisper(self, user: User, message: str) -> None:
        """On a received room whisper."""
        if message.startswith('اثير') and user.username == "60W":
            try:
                xxx = message[2:]
                await self.highrise.chat(xxx)
                await self.highrise.send_emote('dance-breakdance')
            except:
                print("error 3")
            pass

    async def on_chat(self, user: User, message: str) -> None:
        """On a received room-wide chat."""
        if "طيرني" in message:
            try:
                emote_id = "emote-float"
                await self.highrise.send_emote(emote_id, user.id)
            except:
                print("error 3")

        if "رقصني" in message:
            try:
                emote_id = random.choice(self.dancs)
                await self.highrise.send_emote(emote_id, user.id)
            except:
