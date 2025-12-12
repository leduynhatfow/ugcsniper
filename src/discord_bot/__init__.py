import json
import asyncio
import aiofiles
from datetime import datetime
import logging
import discord
from discord.ext import commands
from collections import deque
import time
import math

async def startdiscord(self):
    try:
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        
        # Phiên bản 1.7.3 không có Intents.message_content, cần dùng privileged intents
        intents.messages = True
        
        bot = commands.Bot(
            description='🔫 Roblox Sniper Bot',
            command_prefix="`",
            self_bot=False,
            intents=intents
        )
        
        # Tắt help command mặc định
        bot.remove_command('help')
        
        # Cache để tránh spam
        command_cooldowns = {}
        RATE_LIMIT = 5  # seconds
        
        def check_cooldown(user_id: int) -> bool:
            current_time = time.time()
            if user_id in command_cooldowns:
                if current_time - command_cooldowns[user_id] < RATE_LIMIT:
                    return False
            command_cooldowns[user_id] = current_time
            return True

        @bot.event
        async def on_ready():
            print(f"✅ Discord bot đã sẵn sàng: {bot.user}")
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.items)} items"
            )
            await bot.change_presence(activity=activity)
            
            # Log async
            async with aiofiles.open("logs.txt", "a", encoding="utf-8") as f:
                await f.write(f"\nMAIN THREAD [{time.strftime('%H:%M:%S', time.localtime())}] started discord bot\n")

        @bot.command(name="add", description="Thêm item vào danh sách snipe")
        async def add_id(ctx, item_id: int):
            if not check_cooldown(ctx.author.id):
                await ctx.send("⏳ Vui lòng đợi 5 giây trước khi dùng lệnh tiếp theo!", delete_after=3)
                return
            
            if ctx.author.id not in self.discord_bot["authorized_users"]:
                await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
                return
            
            if item_id in self.items:
                await ctx.send(f"⚠️ Item `{item_id}` đã có trong danh sách!")
                return
            
            # Thêm vào memory
            if self.add_item(item_id):
                # Cập nhật config file async
                try:
                    async with aiofiles.open("config.json", "r", encoding="utf-8") as f:
                        data = json.loads(await f.read())
                    
                    if item_id not in data["items"]:
                        data["items"].append(item_id)
                        
                    async with aiofiles.open("config.json", "w", encoding="utf-8") as f:
                        await f.write(json.dumps(data, indent=4))
                        
                    embed = discord.Embed(
                        title="✅ Thêm thành công",
                        description=f"Đã thêm item `{item_id}` vào danh sách snipe",
                        color=0x00ff00  # Màu xanh lá
                    )
                    embed.add_field(name="Tổng items", value=f"`{len(self.items)}`", inline=False)
                    embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}")
                    
                    await ctx.send(embed=embed)
                    
                except Exception as e:
                    print(f"Config update error: {e}")
                    await ctx.send(f"❌ Lỗi khi cập nhật config: {e}")
            else:
                await ctx.send("❌ Lỗi khi thêm item!")

        @bot.command(name="remove", description="Xóa item khỏi danh sách snipe")
        async def remove_id(ctx, item_id: int):
            if not check_cooldown(ctx.author.id):
                await ctx.send("⏳ Vui lòng đợi 5 giây trước khi dùng lệnh tiếp theo!", delete_after=3)
                return
            
            if ctx.author.id not in self.discord_bot["authorized_users"]:
                await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
                return
            
            if item_id not in self.items:
                await ctx.send(f"⚠️ Item `{item_id}` không có trong danh sách!")
                return
            
            # Xóa khỏi memory
            if self.remove_item(item_id):
                # Cập nhật config file async
                try:
                    async with aiofiles.open("config.json", "r", encoding="utf-8") as f:
                        data = json.loads(await f.read())
                    
                    if item_id in data["items"]:
                        data["items"].remove(item_id)
                        
                    async with aiofiles.open("config.json", "w", encoding="utf-8") as f:
                        await f.write(json.dumps(data, indent=4))
                        
                    embed = discord.Embed(
                        title="✅ Xóa thành công",
                        description=f"Đã xóa item `{item_id}` khỏi danh sách snipe",
                        color=0xff9900  # Màu cam
                    )
                    embed.add_field(name="Tổng items", value=f"`{len(self.items)}`", inline=False)
                    embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}")
                    
                    await ctx.send(embed=embed)
                    
                except Exception as e:
                    print(f"Config update error: {e}")
                    await ctx.send(f"❌ Lỗi khi cập nhật config: {e}")
            else:
                await ctx.send("❌ Lỗi khi xóa item!")

        @bot.command(name="list", description="Xem danh sách items đang snipe")
        async def list_items(ctx, page: int = 1):
            if not check_cooldown(ctx.author.id):
                await ctx.send("⏳ Vui lòng đợi 5 giây trước khi dùng lệnh tiếp theo!", delete_after=3)
                return
            
            if ctx.author.id not in self.discord_bot["authorized_users"]:
                await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
                return
            
            if not self.items:
                await ctx.send("📭 Danh sách items trống!")
                return
            
            items_per_page = 15
            total_pages = math.ceil(len(self.items) / items_per_page)
            page = max(1, min(page, total_pages))
            
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            
            items_slice = self.items[start_idx:end_idx]
            
            embed = discord.Embed(
                title="📋 Danh sách Items",
                description=f"Trang {page}/{total_pages} | Tổng: {len(self.items)} items",
                color=0x0080ff  # Màu xanh dương
            )
            
            # Hiển thị items dạng list
            items_str = ""
            for idx, item_id in enumerate(items_slice, start=start_idx+1):
                items_str += f"{idx}. `{item_id}`\n"
            
            embed.add_field(name="Items", value=items_str or "Không có items", inline=False)
            
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}")
            
            await ctx.send(embed=embed)

        @bot.command(name="status", description="Xem trạng thái sniper")
        async def status(ctx):
            if not check_cooldown(ctx.author.id):
                await ctx.send("⏳ Vui lòng đợi 5 giây trước khi dùng lệnh tiếp theo!", delete_after=3)
                return
            
            if ctx.author.id not in self.discord_bot["authorized_users"]:
                await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
                return
            
            try:
                # Lấy metrics từ sniper
                metrics = {}
                if hasattr(self, 'metrics_dashboard') and callable(getattr(self.metrics_dashboard, 'get_metrics', None)):
                    metrics = self.metrics_dashboard.get_metrics()
                
                embed = discord.Embed(
                    title="📊 Trạng thái Sniper",
                    color=0x8000ff,  # Màu tím
                    timestamp=datetime.now()
                )
                
                # Thông tin cơ bản
                embed.add_field(
                    name="📈 Thống kê",
                    value=f"**Tổng tìm kiếm:** `{self.totalSearches}`\n"
                          f"**Items đang theo dõi:** `{len(self.items)}`\n"
                          f"**Mua thành công:** `{len(self.buyLogs)}`\n"
                          f"**Lỗi gần đây:** `{len(self.errorLogs)}`",
                    inline=False
                )
                
                # Performance
                embed.add_field(
                    name="⚡ Hiệu suất",
                    value=f"**V1 Speed:** `{self.v1search}ms`\n"
                          f"**V2 Speed:** `{self.v2search}ms`\n"
                          f"**Uptime:** `{metrics.get('uptime', 'N/A')}`",
                    inline=True
                )
                
                # Proxy status
                if self.proxy_enable:
                    active_proxies = 0
                    for proxy in self.proxies:
                        metrics_obj = self.proxy_metrics.get(proxy)
                        if metrics_obj:
                            status = metrics_obj.get_status()
                            if status.value in ['healthy', 'degraded']:
                                active_proxies += 1
                    
                    embed.add_field(
                        name="🌐 Proxy",
                        value=f"**Hoạt động:** `{active_proxies}/{len(self.proxies)}`\n"
                              f"**Tỷ lệ thành công:** `{metrics.get('avg_proxy_success', 0):.1f}%`",
                        inline=True
                    )
                
                # Logs gần đây (giới hạn)
                if self.searchLogs:
                    recent_searches = "\n".join(self.searchLogs[-3:])
                    if len(recent_searches) > 500:
                        recent_searches = recent_searches[-500:] + "..."
                    embed.add_field(
                        name="🔍 Tìm kiếm gần đây",
                        value=f"```{recent_searches}```",
                        inline=False
                    )
                
                if self.buyLogs:
                    recent_buys = "\n".join(self.buyLogs[-3:])
                    if len(recent_buys) > 500:
                        recent_buys = recent_buys[-500:] + "..."
                    embed.add_field(
                        name="🛒 Mua hàng gần đây",
                        value=f"```{recent_buys}```",
                        inline=False
                    )
                
                # Avatar trong phiên bản 1.7.3
                avatar_url = ctx.author.avatar_url if hasattr(ctx.author, 'avatar_url') else None
                embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=avatar_url)
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                print(f"Status command error: {e}")
                await ctx.send(f"❌ Lỗi khi lấy trạng thái: {str(e)[:100]}")

        @bot.command(name="clearerrors", description="Xóa logs lỗi")
        async def clear_errors(ctx):
            if ctx.author.id not in self.discord_bot["authorized_users"]:
                await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
                return
            
            self.errorLogs.clear()
            if hasattr(self, 'autosearch_errors'):
                self.autosearch_errors.clear()
            
            embed = discord.Embed(
                title="🧹 Đã xóa logs lỗi",
                color=0x00ff00
            )
            await ctx.send(embed=embed)

        @bot.command(name="help", description="Hiển thị hướng dẫn")
        async def help_command(ctx):
            embed = discord.Embed(
                title="🤖 Sniper Bot Help",
                description="Danh sách lệnh có sẵn:",
                color=0x0080ff
            )
            
            commands_list = [
                ("`add <item_id>`", "Thêm item vào danh sách snipe"),
                ("`remove <item_id>`", "Xóa item khỏi danh sách"),
                ("`list [page]`", "Xem danh sách items (phân trang)"),
                ("`status`", "Xem trạng thái sniper"),
                ("`clearerrors`", "Xóa logs lỗi"),
                ("`help`", "Hiển thị hướng thẫn này")
            ]
            
            for cmd, desc in commands_list:
                embed.add_field(name=cmd, value=desc, inline=False)
            
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}")
            
            await ctx.send(embed=embed)

        @bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                await ctx.send("❌ Lệnh không tồn tại! Gõ `help` để xem danh sách lệnh.")
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"❌ Thiếu tham số! Sử dụng: `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`")
            elif isinstance(error, commands.BadArgument):
                await ctx.send("❌ Tham số không hợp lệ!")
            else:
                print(f"Command error: {error}")
                await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)[:100]}...")

        # Start bot
        await bot.start(self.discord_bot["token"])
        
    except discord.LoginFailure:
        print("❌ Discord token không hợp lệ!")
    except Exception as e:
        print(f"❌ Lỗi khởi động Discord bot: {e}")
        raise