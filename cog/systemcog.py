import discord
from discord import app_commands
from discord.ext import commands

from typing import Literal
import traceback

import numpy

NAKARE = 0  # サーバーのID
DEV_ID = 0  # 開発者のID


async def monica_error(ctx: discord.Interaction, error: Exception):
    embed = discord.Embed(
        title="エラーが発生したのだ。", url="https://www.youtube.com/watch?v=C9PFVo1FEwU")
    embed.add_field(name="エラー発生サーバー名", value=ctx.guild.name, inline=False)
    embed.add_field(name="エラー発生サーバーID", value=ctx.guild.id, inline=False)
    embed.add_field(name="エラー発生ユーザー名", value=ctx.user.name, inline=False)
    embed.add_field(name="エラー発生ユーザーID", value=ctx.user.id, inline=False)
    embed.add_field(name="エラー発生コマンド", value=ctx.command.name, inline=False)

    t = f"```py\n{''.join(traceback.format_exception(error))}```"
    embed.add_field(name="発生エラー", value=t if len(
        t) < 1024 else f"```py\n{error}\n```", inline=False)
    embed.set_footer(text="エラーID: " + numpy.base_repr(ctx.id, 36))
    embed.description = f"何らかのエラーが発生しました。\nこのエラーについて問い合わせるときは下記のエラーIDと合わせて<@{DEV_ID}>へお知らせください"

    try:
        await ctx.response.send_message(embed=embed)
    except discord.InteractionResponded:
        await ctx.channel.send(embed=embed)


class SystemCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.on_app_command_error = bot.tree.error(self.on_app_command_error)
        self.on_command_error = bot.event(self.on_command_error)

    @staticmethod
    async def on_app_command_error(ctx: discord.Interaction, error: app_commands.AppCommandError):
        await monica_error(ctx, error)

    @staticmethod
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(embed=discord.Embed(title="エラーが発生したのだ。",
                                               description="そのコマンドは見つかりませんでした。ごめんなさい。"))
        elif isinstance(error, commands.NotOwner):
            await ctx.send(embed=discord.Embed(title="エラーが発生したのだ。",
                                               description="そのコマンドの権限がないのだ。ごめんなさい。"))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title="エラーが発生したのだ。",
                                               description="パラメータが不足しています。ヘルプコマンドなどで確認してください。"))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=discord.Embed(title="エラーが発生したのだ。",
                                               description=f"現在クールダウン中です...\nあと{error.retry_after}秒後に再試行してください。"))
        else:
            embed = discord.Embed(title="エラー情報", description="")
            embed.add_field(name="エラー発生サーバー名",
                            value=ctx.guild.name, inline=False)
            embed.add_field(name="エラー発生サーバーID",
                            value=ctx.guild.id, inline=False)
            embed.add_field(name="エラー発生ユーザー名",
                            value=ctx.author.name, inline=False)
            embed.add_field(name="エラー発生ユーザーID",
                            value=ctx.author.id, inline=False)
            embed.add_field(name="エラー発生コマンド",
                            value=ctx.message.content, inline=False)

            t = f"```py\n{''.join(traceback.TracebackException.from_exception(error))}```"
            embed.add_field(name="発生エラー", value=t if len(
                t) < 2048 else f"```py\n{error}\n```", inline=False)

            m = await ctx.send(embed=embed)
            await ctx.send(discord.Embed(title="エラーが発生しました",
                                         description="何らかのエラーが発生しました。ごめんなさい。\nこのエラーについて問い合わせるときは下記のエラーIDも一緒にお知らせください")
                           .set_footer(text=numpy.base_repr(m.id, 36)))

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Literal["~", "*", "^"] | None = None) -> None:
        if not guilds:
            m = await ctx.reply("同期中...")
            if spec == "~":  # ギルドコマンドのみを同期
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
                await m.edit(content=f"> {len(synced)}個のギルドコマンドを同期しました。")
            elif spec == "*":  # グローバルコマンドをギルドコマンドにコピー → ギルドコマンドを同期
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
                await m.edit(content=f"> {len(synced)}個のグローバルコマンドをギルドにコピー同期しました。")
            elif spec == "^":  # ギルドコマンドのみを削除 → ギルドコマンドのみを同期
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                await m.edit(content="> ギルドコマンドを全て削除しました。")
            else:  # グローバルコマンドを同期
                synced = await ctx.bot.tree.sync()
                await m.edit(content=f"> {len(synced)}個のグローバルコマンドを同期しました。")
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"> {ret}/{len(guilds)}のギルドでギルドコマンドを同期しました。")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SystemCog(bot))
