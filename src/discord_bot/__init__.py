import json
import asyncio
import aiofiles
from datetime import datetime
import logging
import discord
from discord.ext import commands
from collections import deque
import time

async def startdiscord(self):
    try:
        intents = discord.Intents.all()
        bot = commands.Bot(description='BOT', command_prefix="`", self_bot=False, intents=intents)

        @bot.event
        async def on_ready():
            with open("logs.txt", "a") as f:
                f.write(f"\nMAIN THREAD [{time.strftime('%H:%M:%S', time.localtime())}] started discord bot")

        @bot.command(description="Add a new item id")
        async def add_id(ctx, item_id: int):
            if ctx.author.id not in self.discord_bot["authorized_users"]:
                return await ctx.send(f"You are not authorized to do this")
            elif item_id in self.items:  # Kiểm tra item_id trong list
                return await ctx.send(f"Item already in list")
            self.items.append(item_id)  # Thêm item_id vào list
            data = json.loads(open("config.json", "r").read())
            data["items"].append(item_id)  # Cập nhật config.json
            open("config.json", "w").write(json.dumps(data, indent=4))
            return await ctx.send(f"Successfully added item id `{item_id}`")

        @bot.command(description="Remove item id")
        async def remove_id(ctx, item_id: int):
            if ctx.author.id not in self.discord_bot["authorized_users"]:
                return await ctx.send(f"You are not authorized to do this")
            elif item_id not in self.items:  # Kiểm tra item_id trong list
                return await ctx.send(f"Item id not in list")
            self.items.remove(item_id)  # Xóa item_id khỏi list
            data = json.loads(open("config.json", "r").read())
            data["items"].remove(item_id)  # Cập nhật config.json
            open("config.json", "w").write(json.dumps(data, indent=4))
            return await ctx.send(f"Removed item id `{item_id}`")

        @bot.command(description="Return stats of the sniper")
        async def status(ctx):
            if ctx.author.id not in self.discord_bot["authorized_users"]:
                return await ctx.send(f"You are not authorized to do this")
            item_list_display = str(self.items[:5]) + ('...' if len(self.items) > 5 else '')
            stats = f"Total Searches: {self.totalSearches}\n\nSearch Logs:\n" + '\n'.join(log for log in self.searchLogs) + f"\nBuy Logs:\n" + '\n'.join(log for log in self.buyLogs) + f"\nitem_list: {item_list_display}\nTotal Items bought: {len(self.buyLogs)}\nError Logs:\n" + '\n'.join(log for log in self.errorLogs)
            return await ctx.send(stats)

        @bot.event
        async def on_application_command_error(ctx, error):
            return await ctx.send(f"An error occurred: {error}")

        await bot.start(self.discord_bot["token"])
    except Exception as e:
        print(e)