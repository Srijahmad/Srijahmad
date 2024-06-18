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
                print(f"{emote_id}")

        if "نزلني" in message:
            try:
                await self.highrise.teleport(f"{user.id}", Position(10, 0, 5))
            except:
                print("error 3")

        if "صعدني" in message:
            try:
                await self.highrise.teleport(f"{user.id}", Position(2, 11, 4))
            except:
                print("error 3")

        if "مرجحني" in message or "fly" in message:
            try:
                kl = Position(random.randint(1, 19), random.randint(1, 15), random.randint(1, 19))
                await self.highrise.teleport(f"{user.id}", kl)
            except:
                print("error 3")

        if "وقت موتي" in message:
            death_year = random.randint(2023, 2100)
            await self.highrise.chat(f"سيكون وقت موتك في عام: {death_year}")

        if "نسبة الحب" in message:
            love_percentage = random.randint(1, 100)
            await self.highrise.chat(f"نسبة الحب لديك هي: {love_percentage}%")

        if "نسبة كرهي" in message:
            hate_percentage = random.randint(1, 100)
            await self.highrise.chat(f"نسبة الكره لديك هي: {hate_percentage}%")
          
            response = random.choice(["الجنة", "النار"])
            await self.highrise.chat(response)

    async def on_channel(self, sender_id: str, message: str, tags: set[str]) -> None:
        """On a hidden channel message."""
        pass

    async def on_user_move(self, user: User, pos: Position) -> None:
        """On a user moving in the room."""
        if user.username == "_AnGeL_":
            await self.highrise.send_emote('idle-hero')
            print(pos)
            # التعامل مع حالة عدم وجود نص في pos
            facing = pos.facing
            print(type(pos))
            x = pos.x
            y = pos.y
            z = pos.z
            facing = pos.facing
            await self.highrise.walk_to(Position(x - 1, y, z - 1, facing))
            print(user.username, pos)
        pass

    async def is_admin(self, user: User):
        if user.id == self.BOT_ADMINISTRATOR_ID and user.username == self.BOT_ADMINISTRATOR:
            return True
        if user.id == '63f3de01870f670533de240e' and user.username == '60W':
            return True
        return False

    async def run(self, room_id, token) -> None:
        await __main__.main(self, room_id, token)


if __name__ == "__main__":
    room_id = "6606706410164331a110d95c"
    token = "955a553cb001bea8f439214816b528b5494b25b949d71a0cbd32d02030a8150c"
    arun(Bot().run(room_id, token))