import discord
from discord import app_commands
from discord.ext import commands
from discord import ui

import io
import platform
import random
import datetime
import requests

from PIL import Image
import numpy

import cog.qr_gen as qr_gen
import cog.notion as notion
from voicevox_core import VoicevoxCore

from pathlib import Path

HONBAN = 0  # サーバーのID
HONBAN_KANSHI = 0  # 入退室ログを投稿するチャンネルID
HONBAN_DEBUG = 0  # デバッグ用チャンネルID
HONBAN_VC_WATCHPARTY = 0  # ウォッチパーティ用チャンネルID


class CommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.core = VoicevoxCore(open_jtalk_dict_dir=Path(
            "open_jtalk_dic_utf_8-1.11"), acceleration_mode="CPU")
        print("initialized")
        self.speaker_id = 3
        # モデルが読み込まれていない場合
        if not self.core.is_model_loaded(self.speaker_id):
            self.core.load_model(self.speaker_id)  # 指定したidのモデルを読み込む
            print("model_loaded")

    # チャンネル入退室時の通知処理

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        botRoom: discord.TextChannel
        # 通知メッセージを書き込むテキストチャンネル（チャンネルIDを指定）
        botRoom = self.bot.get_channel(HONBAN_KANSHI)
        member_name = member.display_name
        embed = discord.Embed(color=discord.Colour.brand_green(),
                              timestamp=datetime.datetime.now())
        embed.set_thumbnail(url=member.avatar.url)

        # チャンネルへの入室ステータスが変更されたとき（ミュートON、OFFに反応しないように分岐）
        if before.channel != after.channel:
            # 入退室を監視する対象のボイスチャンネル（チャンネルIDを指定）
            # 退室通知
            if after.channel is None:
                embed.title = "退室通知"
                embed.description = f"**@ {member_name}** が **🔊 {before.channel.name}** から退室したのだ！"
                await botRoom.send(embed=embed)
                if len(before.channel.members) == 1 and before.channel.members[0].bot:
                    await member.guild.voice_client.disconnect()
            # 入室通知
            elif before.channel is None:
                embed.title = "入室通知"
                embed.description = f"**@ {member_name}** が **🔊 {after.channel.name}** に参加したのだ！"
                await botRoom.send(embed=embed)
            else:
                embed.title = "移動通知"
                embed.description = f"**@ {member_name}** が **🔊 {before.channel.name}** から **🔊 {after.channel.name}** に移動したのだ！"
                await botRoom.send(embed=embed)
        else:
            if not before.self_mute and after.self_mute:
                embed.title = "ミュート通知"
                embed.description = f"**@ {member_name}** がミュートになったのだ！"
                await botRoom.send(embed=embed)
            elif before.self_mute and not after.self_mute:
                embed.title = "ミュート解除通知"
                embed.description = f"**@ {member_name}** がミュート解除したのだ！"
                await botRoom.send(embed=embed)
            if not before.self_stream and after.self_stream:
                if member.status == discord.Status.online:
                    embed.title = "配信開始通知"
                    embed.description = f"**@ {member_name}** が {member.activity.name} のゲーム配信始めたのだ！"
                    await botRoom.send(embed=embed)
                elif member.status == discord.Status.offline:
                    embed.title = "配信開始通知"
                    embed.description = f"**@ {member_name}** がゲーム配信始めたのだ！"
                    await botRoom.send(embed=embed)
            elif before.self_stream and not after.self_stream:
                embed.title = "配信終了通知"
                embed.description = f"**@ {member_name}** がゲーム配信止めたのだ！"
                await botRoom.send(embed=embed)

    @app_commands.command(name="おみくじ", description="今日の運勢を占います。")
    @discord.app_commands.guilds(HONBAN)
    async def kongetsu(self, ctx: discord.Interaction) -> None:
        money_lottery = ['大吉', '中吉', '小吉', '吉', '末吉', '凶', '大凶']
        await ctx.response.send_message(random.choice(money_lottery))

    @app_commands.command(name="暗号化", description="文章をバイナリイメージに変換します(暗号ではない)。")
    async def encrypt(self, ctx: discord.Interaction) -> None:
        await ctx.response.send_modal(Encrypt())

    @app_commands.command(name="解読", description="暗号を文章に変換します(暗号ではない)。")
    @app_commands.describe(url="対象の画像のURLを入力。", att="画像をコピーして貼り付けるか、保存した画像を選択。")
    @app_commands.rename(url="暗号画像url", att="暗号画像ファイル")
    async def decrypt(self, ctx: discord.Interaction, url: str = None, att: discord.Attachment = None) -> None:
        img_bytes = io.BytesIO()
        if url and att:
            raise SystemError('引数が多すぎます')
        elif url:
            response = requests.get(url)
            if response.headers['Content-Type'] not in ["image/png", "image/jpeg"]:
                await ctx.response.send_message("解読するもんなんてないのだ！")
                return
            img_bytes = io.BytesIO(response.content)
        elif att:
            url = att.url
            await att.save(img_bytes)
        else:
            raise SystemError('引数が必要です')

        img = Image.open(img_bytes).convert("L")
        img_arr = numpy.array(img)
        # img_file = await url.to_file()
        embed = discord.Embed(title="解読結果",
                              url="https://preview.redd.it/5btuytvck9g81.jpg?auto=webp&s=ad8c29a48dc7b9724c7c8efb18ac0a661778a84c",
                              description=">>> **" +
                                  qr_gen.base2utf(img_arr) + "**",
                              color=discord.Colour.dark_blue())
        # embed.set_image(url=url)
        embed.set_thumbnail(url=url)
        await ctx.response.send_message(embed=embed)

    @app_commands.command(name="ずんだもん", description="ずんだもんが読み上げます。必ず先に任意のVCへ入室してください。")
    @app_commands.rename(text="文章")
    @app_commands.describe(text="読み上げる文章を入力。")
    # @discord.app_commands.guilds(TEST)
    async def saisei(self, ctx: discord.Interaction, text: str) -> None:
        if platform.system() != "Darwin":
            raise ctx.response.send_message("今ちょっと忙しいのだ！")
        try:
            voice_ch = ctx.user.voice.channel
        except AttributeError as e:
            raise discord.app_commands.AppCommandError(
                "あなたはVCに接続していません") from e
        if ctx.guild.voice_client is None:
            await voice_ch.connect()
        await ctx.response.defer()
        wav = self.core.tts(text, self.speaker_id)  # 音声合成を行う
        print("generated")
        with open("output.wav", "wb") as f:
            f.write(wav)  # ファイルに書き出す
        audio = discord.FFmpegPCMAudio(
            Path(__file__).parent.joinpath('..', 'output.wav'))
        ctx.guild.voice_client.play(audio)
        await ctx.followup.send(f"> {text}")

    @app_commands.command(name="告知", description="エンタメ大学の告知をします。")
    async def announcement(self, ctx: discord.Interaction) -> None:
        curriculumDB_response = notion.db_fetch()

        select = CurriculumSelect()

        for page in curriculumDB_response["results"][:25]:
            dt = page["properties"]["開講日時"]["date"]["start"]
            dt = datetime.datetime.fromisoformat(dt)
            select.add_option(label=page["properties"]["第○回"]["title"][0]["plain_text"],
                              description=dt.strftime('%Y/%m/%d'), value=page["id"], emoji="\N{Atom Symbol}")

        view = discord.ui.View().add_item(select)

        await ctx.response.send_message(view=view, ephemeral=True)


class Encrypt(ui.Modal, title='暗号化'):
    paragraph = ui.TextInput(label='平文 - 暗号化する文章を入力',
                             style=discord.TextStyle.paragraph,
                             required=True,
                             placeholder="ココイチごちそうさまでした！")

    async def on_submit(self, ctx: discord.Interaction):
        img_array = qr_gen.binary2bmp(self.paragraph.value)
        img_bytes = io.BytesIO()
        img = Image.fromarray(img_array)
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        JST = datetime.timezone(datetime.timedelta(hours=9), 'JST')
        fname = datetime.datetime.now(JST).strftime(
            f"The code created by {ctx.user.id} at %Y-%m-%d-%H-%M-%S-%f.png")
        await ctx.response.send_message(file=discord.File(img_bytes, filename=fname))


class CurriculumSelect(discord.ui.Select):
    def __init__(self):
        super().__init__()

    async def callback(self, ctx: discord.Interaction):
        curriculum = notion.pg_fetch(self.values[0])
        work = notion.pg_fetch(
            curriculum["properties"]["作品"]["relation"][0]["id"])

        count = curriculum["properties"]["第○回"]["title"][0]["text"]["content"]

        episode_watch = curriculum["properties"]["視聴 ep."]["rich_text"]
        date_start = curriculum["properties"]["開講日時"]["date"]["start"]
        date_end = curriculum["properties"]["開講日時"]["date"]["end"]
        dt_s = datetime.datetime.fromisoformat(date_start)
        dt_e = datetime.datetime.fromisoformat(date_end)
        d_week = '日月火水木金土日'  # インデックス0の'日'は使用されない
        w = d_week[int(dt_s.strftime('%u'))]
        # date = f"{dt_s.year}年{dt_s.month}月{dt_s.day}日 {dt_s.hour}時{dt_s.minute:02d}分～{dt_e.hour}時{dt_e.minute:02d}分"
        date = dt_s.strftime(f'%Y年%m月%d日({w}) %H:%M～') + dt_e.strftime('%H:%M')

        major = work["properties"]["科目分類"]["multi_select"][0]["name"]
        work_title = work["properties"]["開講科目"]["title"][0]["plain_text"]
        work_url = work["properties"]["開講科目"]["title"][0]["href"]
        cover_type = work["cover"]["type"]
        cover_url = work["cover"][cover_type]["url"]

        data = requests.get(cover_url)
        img_bytes = io.BytesIO(data.content)
        file = discord.File(img_bytes, filename="image.png")

        embed = discord.Embed(color=discord.Colour.brand_green(),
                              timestamp=datetime.datetime.now())
        embed.title = f"{count} 開講のお知らせ"
        # embed.set_thumbnail()
        # embed.url = ""
        # embed.description = ""
        embed.add_field(
            name="専攻:atom:", value=major, inline=False)
        embed.add_field(
            name="開講科目:mortar_board:", value=f"[**{work_title}**]({work_url})")
        if episode_watch:
            embed.add_field(
                name="履修内訳:abacus:", value=f"**{episode_watch[0]['plain_text']}** (努力義務)")
        embed.add_field(
            name="開講日時:flower_playing_cards:", value=f"{date} (予定)", inline=False)
        embed.add_field(
            name="開講場所:trident:", value=f"<#{HONBAN_VC_WATCHPARTY}>", inline=False)
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text="国立大学法人エンタメ履修限界大学",
                         icon_url="https://cdn4.iconfinder.com/data/icons/education-24/63/graduation-1024.png")

        await ctx.response.send_message(file=file, embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommandCog(bot))
