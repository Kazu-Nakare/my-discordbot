import discord
from discord.ext import commands
import asyncio
import logging
# from memory_profiler import profile

bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())
logging.basicConfig(level=logging.INFO)


with open('token.txt', 'r', encoding="utf-8") as f:
    token = f.read()

cogs = ["cog.systemcog", "cog.commandcog"]

# cogの更新


@bot.command()
@commands.is_owner()
async def re(ctx: commands.Context) -> None:
    try:
        for cog in cogs:
            print(f"{cog} を再読み込み")
            await bot.reload_extension(cog)
    except (commands.ExtensionNotLoaded, commands.ExtensionNotFound, commands.NoEntryPointError) as e:
        print(e)
    except commands.ExtensionFailed as e:
        print(e.original)
    else:
        await ctx.reply("> **更新完了なのだ！**")


@bot.event
async def on_ready():
    print("Bot起動")


# @profile
async def main():
    async with bot:
        try:
            for cog in cogs:
                await bot.load_extension(cog)
        except (commands.ExtensionNotLoaded, commands.ExtensionNotFound, commands.NoEntryPointError) as e:
            print(e)
        except commands.ExtensionFailed as e:
            print(e.original)
        else:
            print("Cog読み込み")

        await bot.start(token)

asyncio.run(main())
