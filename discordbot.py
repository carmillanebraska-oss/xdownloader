pip install discord
import discord
from discord.ext import commands
import requests
import re
from urllib.parse import urljoin
import asyncio

# Configurações
TOKEN = "MTQ3MzEyMjAzNDUwOTgwNzYxNg.GFLkrO.rpQgkki3rbSsjy05g6j4vMrn6fYXDNrIi70H9Q"  # ← cole aqui entre aspas!

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def extrair_urls_xvideos(url_pagina: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.xvideos.com/"
    }
    try:
        r = requests.get(url_pagina, headers=headers, timeout=12)
        r.raise_for_status()
        html = r.text

        urls = {}
        padroes = [
            r"html5player\.setVideoUrlHigh\(['\"]([^'\"]+)['\"]\s*,",
            r"html5player\.setVideoUrlLow\(['\"]([^'\"]+)['\"]\s*,",
            r"html5player\.setVideoHLS\(['\"]([^'\"]+)['\"]\s*,",
            r"['\"](https?://[^'\"]+\.mp4\?[^'\"]*?)['\"]",
        ]

        for padrao in padroes:
            for match in re.findall(padrao, html):
                u = match.strip()
                if not u.startswith("http"):
                    u = urljoin(url_pagina, u)
                if "mp4" in u.lower() or "m3u8" in u.lower():
                    if   "1080" in u: res = "1080p"
                    elif "720"  in u: res = "720p"
                    elif "480"  in u: res = "480p"
                    elif "360"  in u: res = "360p"
                    elif "240"  in u: res = "240p"
                    else:             res = "outra"
                    urls[res] = u

        if not urls:
            mp4s = re.findall(r'(https?://[^\'"\s]+?\.mp4\?[^\'"\s<]+)', html)
            for u in mp4s:
                if "cdn" in u and "secure=" in u:
                    urls["provavel"] = u

        return urls
    except Exception as e:
        print(f"Erro extraindo: {e}")
        return {}


@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")


@bot.command(name="baixar")
async def cmd_baixar(ctx, url: str):
    """!baixar <link do xvideos>"""
    msg = await ctx.send(f"Buscando resoluções disponíveis para:\n{url}")

    urls = await extrair_urls_xvideos(url)
    if not urls:
        await msg.edit(content="Não encontrei links de vídeo direto nessa página. O site pode ter mudado a forma como entrega os vídeos.")
        return

    # Ordena as resoluções (melhor primeiro)
    ordem_res = ["1080p", "720p", "480p", "360p", "240p", "outra", "provavel"]
    res_disponiveis = [r for r in ordem_res if r in urls]

    if not res_disponiveis:
        res_disponiveis = list(urls.keys())

    # Monta lista de opções
    texto_opcoes = "Resoluções encontradas:\n"
    for i, res in enumerate(res_disponiveis, 1):
        texto_opcoes += f"{i}) {res.upper()}\n"

    await msg.edit(
        content=(
            f"Escolha a resolução desejada respondendo com o número (1, 2, 3...):\n\n"
            f"{texto_opcoes}\n"
            f"Ou digite 'cancelar' para desistir.\n"
            f"Você tem 60 segundos."
        )
    )

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and (
            m.content.isdigit() or m.content.lower() == "cancelar"
        )

    try:
        resposta = await bot.wait_for("message", check=check, timeout=60.0)

        if resposta.content.lower() == "cancelar":
            await resposta.reply("Operação cancelada.")
            await msg.delete()
            return

        escolha = int(resposta.content)
        if 1 <= escolha <= len(res_disponiveis):
            res_escolhida = res_disponiveis[escolha - 1]
            link_final = urls[res_escolhida]

            await resposta.reply(
                f"Link direto da resolução {res_escolhida.upper()}:\n"
                f"\n{link_final}\n\n"
            )
            await msg.delete()
        else:
            await resposta.reply("Número fora da lista. Use !baixar novamente para tentar de novo.")
            await msg.delete()

    except asyncio.TimeoutError:
        await msg.edit(content="Tempo esgotado (60 segundos). Use !baixar novamente se quiser.")
    except Exception as e:
        await ctx.send(f"Erro: {str(e)}")


bot.run(TOKEN)
