import os, asyncio, time, json, re, random
from datetime import datetime
from telethon import TelegramClient, events

try:
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    OWNER_ID = int(os.environ.get("OWNER_ID"))
    TARGET_GROUP_ID = int(os.environ.get("TARGET_GROUP_ID"))
    LOG_GROUP_ID = int(os.environ.get("LOG_GROUP_ID"))
except (TypeError, ValueError):
    print("❌ ERROR: Periksa kembali variabel di Railway!")
    exit(1)

bot = TelegramClient('bot_official_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
FILE_DB = "partners_database.json"
tagall_queue = asyncio.Queue()
is_processing = False

EMOJIS = ["👑","🔥","⭐","🚀","💎","✨","🎯","⚡","🔮","🍕","🍃","🪐","🎈","🎉","🎐","🍭","👾","🧸","🦊","🐼","🐸","🦄","🍀","🍒","🍇","🥑","🎀","🔑","🛡️","🧬","🛸","🍿","🎵","🎸","🎲","🎰","🗽","🗼","🏰","🌊"]

def load_partners():
    if os.path.exists(FILE_DB):
        try:
            with open(FILE_DB, "r") as f: return json.load(f)
        except: return []
    return []

def save_partners(data):
    with open(FILE_DB, "w") as f: json.dump(data, f, indent=4)

PARTNERS_LIST = load_partners()
print("⚡ Bot Siap!")

@bot.on(events.NewMessage(pattern=r'(?i)^/addpartner(.*)'))
async def add_partner(event):
    global PARTNERS_LIST
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    l_baru = event.pattern_match.group(1).strip()
    if not l_baru or not l_baru.startswith(("http", "t.me")):
        return await event.respond("⚠️ Gunakan format link yang benar!")
    if l_baru in PARTNERS_LIST: return await event.respond("⚠️ Sudah ada!")
    PARTNERS_LIST.append(l_baru)
    save_partners(PARTNERS_LIST)
    await event.respond("✅ Berhasil ditambah!")

@bot.on(events.NewMessage(pattern=r'(?i)^/delpartner(.*)'))
async def del_partner(event):
    global PARTNERS_LIST
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    inp = event.pattern_match.group(1).strip()
    if not inp: return
    if inp.isdigit():
        idx = int(inp) - 1
        if 0 <= idx < len(PARTNERS_LIST):
            PARTNERS_LIST.pop(idx)
            save_partners(PARTNERS_LIST)
            await event.respond("🗑️ Dihapus!")
    else:
        if inp in PARTNERS_LIST:
            PARTNERS_LIST.remove(inp)
            save_partners(PARTNERS_LIST)
            await event.respond("🗑️ Dihapus!")

@bot.on(events.NewMessage(pattern=r'(?i)^/listpartner'))
async def list_partner(event):
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    if not PARTNERS_LIST: return await event.respond("📂 Kosong!")
    txt = "📋 **PARTNER AKTIF:**\n"
    for i, l in enumerate(PARTNERS_LIST, start=1): txt += f"{i}. {l}\n"
    await event.respond(txt, link_preview=False)

async def process_queue():
    global is_processing
    is_processing = True
    while not tagall_queue.empty():
        task = await tagall_queue.get()
        pemicu, teks, mitra, nama, user = task['p'], task['t'], task['m'], task['n'], task['u']
        try:
            await bot.send_message(pemicu, "🚀 **GILIRAN ANDA DIMULAI!**")
        except: pass
        try:
            chat = await bot.get_entity(TARGET_GROUP_ID)
            i_msg = await bot.send_message(TARGET_GROUP_ID, f"🚀 **TAGALL DIMULAI**\n👥 **GROUP:** {chat.title}", link_preview=False)
            ids = [i_msg.id]
        except:
            tagall_queue.task_done()
            continue
        try:
            await bot.send_message(LOG_GROUP_ID, f"📝 **Tagall Dimulai**\n👤 {nama} (@{user})\n🤝 {mitra}\n💬 {teks}", link_preview=False)
        except: pass
        mentions = []
        try:
            async for u in bot.iter_participants(TARGET_GROUP_ID):
                if not u.bot: mentions.append(f"[{random.choice(EMOJIS)}](tg://user?id={u.id})")
        except: pass
        if not mentions:
            tagall_queue.task_done()
            continue
        chunks = [mentions[i:i + 5] for i in range(0, len(mentions), 5)]
        t_start = time.time()
        l_sent = False
        w_habis = False
        for chunk in chunks:
            if int(time.time() - t_start) not in range(0, 300):
                w_habis = True
                break
            try:
                m_tag = await bot.send_message(TARGET_GROUP_ID, f"{teks}\n\n" + " ".join(chunk), parse_mode='md')
                ids.append(m_tag.id)
            except: pass
            await asyncio.sleep(3.5)
            if int(time.time() - t_start) not in range(0, 60) and not l_sent:
                try:
                    await bot.send_message(pemicu, "📊 **BERJALAN 1 MENIT!**")
                    l_sent = True
                except: pass
        durasi = round((time.time() - t_start) / 60)
        d_txt = f"{durasi}m" if durasi != 0 else f"{round(time.time() - t_start)}s"
        t_txt = "Selesai (Limit 5m)" if w_habis else "Selesai"
        try:
            s_msg = await bot.send_message(TARGET_GROUP_ID, f"✅ **{t_txt}!** Pesan sampah dihapus dalam 5 menit...")
            ids.append(s_msg.id)
        except: pass
        try:
            await bot.send_message(LOG_GROUP_ID, f"🟢 **Tagall Selesai**\n👤 {nama}\n🤝 {mitra}\n⏳ {t_txt}", link_preview=False)
        except: pass
        p_bytes = None
        try:
            p_bytes = await bot.download_profile_photo(TARGET_GROUP_ID, file=bytes)
        except: pass
        bukti = f"━━━━━━━━━━━━━━━━━━━━\n**TAGALL SELESAI**\n━━━━━━━━━━━━━━━━━━━━\n📆 **TANGGAL :** `{datetime.now().strftime('%d-%m-%Y %H:%M')}`\n🏰 **GROUP :** **{chat.title}**\n🤝 **PARTNER :** {mitra}\n📩 **TERKIRIM :** `{len(mentions)}`\n⏳ **DURASI :** `{d_txt}`\n━━━━━━━━━━━━━━━━━━━━\n**teruskan pesan ini sebagai bukti!!!**"
        try:
            if p_bytes: await bot.send_file(pemicu, file=p_bytes, caption=bukti, parse_mode='md')
            else: await bot.send_message(pemicu, bukti, parse_mode='md', link_preview=False)
        except: pass
        tagall_queue.task_done()
        asyncio.create_task(clean_delayed(ids))
    is_processing = False

async def clean_delayed(ids):
    await asyncio.sleep(300)
    try:
        await bot.delete_messages(TARGET_GROUP_ID, ids)
        await bot.send_message(OWNER_ID, f"🧹 **BERSIH:** {len(ids)} pesan dihapus!")
    except: pass

@bot.on(events.NewMessage(incoming=True))
async def handle_public_auto_tagall(event):
    if not event.is_private or event.text.startswith("/"): return
    urls = re.findall(r'(https?://\S+|t\.me/\S+)', event.text)
    if not urls: return await event.respond("❌ Tidak ada link partner!")
    v_link = ""
    for url in urls:
        clean = url.strip().rstrip(".,;)")
        if clean in PARTNERS_LIST:
            v_link = clean
            break
    if not v_link: return await event.respond("❌ Link tidak terdaftar!")
    s = await event.get_sender()
    n = s.first_name if s.first_name else "User"
    u = s.username if s.username else "tidak_ada"
    q_idx = tagall_queue.qsize()
    await tagall_queue.put({'p': event.sender_id, 't': event.text, 'm': v_link, 'n': n, 'u': u})
    if is_processing: await event.respond(f"⏳ Masuk antrian ke-{q_idx + 1}!")
    else:
        await event.respond("✅ Terverifikasi! Memulai bot...")
        asyncio.create_task(process_queue())

bot.run_until_disconnected()
