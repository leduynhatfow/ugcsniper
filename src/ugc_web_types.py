import re

class message:
    async def check_message(self, event):
        try:
            embeds = event["d"].get("embeds", [])
            if not embeds and "message_snapshots" in event["d"]:
                try:
                    embeds = event["d"]["message_snapshots"][0]["message"].get("embeds", [])
                    if self.nitro_sniper_obj:
                        self.nitro_sniper_obj.log_search("Found embeds in message_snapshots")
                except (IndexError, KeyError, TypeError) as e:
                    if self.nitro_sniper_obj:
                        self.nitro_sniper_obj.log_error(f"Failed to parse message_snapshots: {e}")
                    embeds = []
            
            valid_urls = []
            for embed in embeds:
                embed_color = embed.get("color", 0)
                if embed_color != 25087:
                    url = embed.get("url", None)
                    if url and url != "No URL":
                        if re.match(r'https?://(www\.)?(roblox\.com/catalog|rolimons\.com/item)/\d+', url):
                            valid_urls.append(url)
                        else:
                            if self.nitro_sniper_obj:
                                self.nitro_sniper_obj.log_search(f"Ignoring invalid URL: {url}")
                else:
                    with open("logs.txt", "a", encoding="utf-8") as f:
                        d = event.get("d", {})
                        snapshots = d.get("message_snapshots", [])

                        if snapshots and "message" in snapshots[0] and "id" in snapshots[0]["message"]:
                            original_id = snapshots[0]["message"]["id"]
                            f.write(f"Skipped {original_id}\n")
                        else:
                            msg_id = d.get("id")
                            f.write(f"Skipped {msg_id} (no snapshot)\n")

            
            if valid_urls:
                if self.nitro_sniper_obj:
                    self.nitro_sniper_obj.log_search(f"Found valid URLs: {valid_urls}")
                return valid_urls[0]
            else:
                if self.nitro_sniper_obj:
                    self.nitro_sniper_obj.log_search("No valid URLs found in embeds")
                return None
        except Exception as e:
            if self.nitro_sniper_obj:
                self.nitro_sniper_obj.log_error(f"Error in check_message: {e}")
            return None