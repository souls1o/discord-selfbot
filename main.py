import discord
from discord.ext import commands
import asyncio
import os
import logging
from typing import Dict, Callable, List, Optional
import re
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('selfbot')

# Configuration
PREFIX = "!"  
TOKEN = os.getenv("DISCORD_TOKEN")  

class CommandHandler:
    """Centralized command registry - remains scalable."""
    def __init__(self):
        self.commands: Dict[str, Callable] = {}
    
    def register(self, name: str, func: Callable):
        self.commands[name] = func
        logger.info(f"Registered command: {name}")
    
    async def execute(self, ctx: commands.Context, args: List[str]) -> bool:
        if not args:
            return False
        cmd_name = args[0].lower()
        if cmd_name in self.commands:
            try:
                await self.commands[cmd_name](ctx, args[1:])
                return True
            except Exception as e:
                logger.error(f"Error in {cmd_name}: {e}")
                await ctx.send(f"Error: {str(e)}", delete_after=5)
                return True
        return False

class SelfBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            self_bot=True,
            help_command=None,
        )
        self.command_handler = CommandHandler()

        # ================== AUTOPOST CONFIG ==================
        self.auto_post_enabled = False
        self.auto_post_channel_name = "lf-players"          # ← Change channel name here
        self.auto_post_message = """
**__3x__ your bet ft5, any 7 total = point to me
__2x__ your bet ft3, any 7 total = point to me
__2x__ your bet ft5, 2-0 lead ft5
__1.5x__ your bet ft3, 1-0 lead
__1.2x__ your bet ft5, i win ties**
        """
        # ====================================================

        self._register_builtin_commands()

    def _register_builtin_commands(self):
        async def ca(ctx: commands.Context, args: List[str]):
            await ctx.send("$youlovejv")
            await ctx.send("Jesse Valdez")

        async def venmo(ctx: commands.Context, args: List[str]):
            await ctx.send("@youlovejesse")
            await ctx.send("Jesse Valdez")

        async def chime(ctx: commands.Context, args: List[str]):
            await ctx.send("$youlovejesse")
            await ctx.send("Jesse Valdez")

        async def btc(ctx: commands.Context, args: List[str]):
            await ctx.send("bc1qvyeszhhdn6v7melz4cl0rp8fl343hvx5ttevph")
        
        async def ltc(ctx: commands.Context, args: List[str]):
            await ctx.send("LR6v74urHAWy8zQioCiEwvvRAf75VUDH8Z")

        async def sol(ctx: commands.Context, args: List[str]):
            await ctx.send("HznFzJNmAuq8ds8dAvpq4rL5xLdc6aQmXscBjP7jjtRr")
        
        async def eth(ctx: commands.Context, args: List[str]):
            await ctx.send("0xA65F50b9d02150A628191bc8B20Ea8C3086543a9")

        async def autopost(ctx, args):
            """Toggle autopost on"""
            if self.auto_post_enabled:
                return
            self.auto_post_enabled = True
            self.auto_post_task = asyncio.create_task(self._autopost_loop())

        async def stopautopost(ctx, args):
            """Toggle autopost off"""
            if not self.auto_post_enabled:
                return
            self.auto_post_enabled = False
            if self.auto_post_task:
                self.auto_post_task.cancel()
                self.auto_post_task = None

        async def reply_calc(ctx, args):
            """!replycalc <message_id> <number> - Replies to a message with calc formats"""
            if len(args) < 2:
                await ctx.send("Usage: !replycalc <message_id> <number>")
                return
            try:
                msg_id = int(args[0])
                num = int(args[1])
            except ValueError:
                await ctx.send("Message ID and number must be integers.")
                return
            
            try:
                original_msg = await ctx.channel.fetch_message(msg_id)
            except discord.NotFound:
                await ctx.send("Message not found.")
                return
            except Exception as e:
                await ctx.send(f"Error fetching message: {e}")
                return
            
            # Generate the two lines
            line1 = f"{num*3}v{num} ft5 any 7 total = point to me"
            line2 = f"{num*2}v{num} ft3 any 7 total = point to me"
            line3 = f"{num*1.5}v{num} ft3 1-0 lead"
            line4 = f"{num*1.2}v{num} ft3 i win ties"
            
            reply_content = f"{line1}\n{line2}"
            await original_msg.reply(reply_content)

        self.command_handler.register("chime", chime)
        self.command_handler.register("ca", ca)
        self.command_handler.register("venmo", venmo)
        self.command_handler.register("btc", btc)
        self.command_handler.register("eth", eth)
        self.command_handler.register("ltc", ltc)
        self.command_handler.register("sol", sol)
        self.command_handler.register("autopost", autopost)
        self.command_handler.register("stopautopost", stopautopost)
        self.command_handler.register("7", reply_calc)

    async def _autopost_loop(self):
        while self.auto_post_enabled:
            try:
                for guild in self.guilds:
                    for channel in guild.channels:
                        if isinstance(channel, discord.TextChannel) and channel.name.lower() == self.auto_post_channel_name.lower():
                            try:
                                await channel.send(self.auto_post_message)
                                logger.info(f"Autoposted to #{channel.name}")
                            except Exception as e:
                                logger.warning(f"Failed to post: {e}")
                await asyncio.sleep(300)  # 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Autopost loop error: {e}")
                await asyncio.sleep(30)

    def add_command(self, name: str, func: Callable):
        self.command_handler.register(name, func)

bot = SelfBot()

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    print(f"Selfbot is ready! Prefix: {PREFIX}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.id != bot.user.id:
        return

    ctx = await bot.get_context(message)
    if ctx.valid and ctx.command:
        await bot.process_commands(message)
        return

    content = message.content.strip()
    if content.startswith(PREFIX):
        try:
            await message.delete()
        except:
            pass
        args = content[len(PREFIX):].strip().split()
        if args:
            await bot.command_handler.execute(ctx, args)

if __name__ == "__main__":
    bot.run(TOKEN)