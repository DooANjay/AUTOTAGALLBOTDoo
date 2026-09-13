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

def build_log_start(a, b, c, d, e, f):
    clean_f = f.replace('\n', '\n>')
    res = f">📝 **Tagall Dimulai**\n>━━━━━━━━━━━━━━━━━━━━\n>👤 **Nama :** {a}\n>🆔 **Username :** @{b}\n>🔢 **ID :** `{c}`\n>⏰ **Jam :** {d}\n>🤝 **Link :** {e}\n>💬 **Pesan :** \n>{clean_f}\n>━━━━━━━━━━━━━━━━━━━━"
    return res

def build_log_done(a, b, c, d, e):
    clean_e = e.replace('\n', '\n>')
    res = f">🟢 **Tagall Selesai**\n>━━━━━━━━━━━━━━━━━━━━\n>👤 **Pengirim :** {a}\n>🤝 **Link :** {b}\n>⏳ **Durasi :** {c}\n>⏰ **Waktu Selesai :** {d}\n>💬 **Pesan :** \n>{clean_e}\n>━━━━━━━━━━━━━━━━━━━━"
    return res

def build_struk(a, b, c, d, e, f):
    res = f">━━━━━━━━━━━━━━━━━━━━\n>**TAGALL SELESAI**\n>━━━━━━━━━━━━━━━━━━━━\n>📆 **TANGGAL :** `{a}`\n>🏰 **GROUP :** **{b}**\n>🤝 **PARTNER :** {c} ({d})\n>📩 **TERKIRIM :** `{e}`\n>⏳ **DURASI :** `{f}`\n>━━━━━━━━━━━━━━━━━━━━\n>**teruskan pesan ini sebagai bukti!!!**"
    return res

def load_partners():
    if os.path.exists(FILE_DB):
        try:
            with open(FILE_DB, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_partners(data):
    with open(FILE_DB, "w") as f: json.dump(data, f, indent=4)

PARTNERS_DICT = load_partners()
print("⚡ Bot Siap!")

@bot.on(events.NewMessage(pattern=r'(?i)^/addpartner(.*)'))
async def add_partner(event):
    global PARTNERS_DICT
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    inp = event.pattern_match.group(1).strip()
    if " - " not in inp: return await event.respond("⚠️ Format salah! Gunakan NAMA - LINK")
    nama_grup, link_baru = inp.split(" - ", 1)
    nama_grup, link_baru = nama_grup.strip(), link_baru.strip()
    if not link_baru.startswith(("http", "t.me")): return await event.respond("⚠️ Link tidak valid!")
    if link_baru in PARTNERS_DICT: return await event.respond("⚠️ Sudah ada!")
    PARTNERS_DICT[link_baru] = nama_grup
    save_partners(PARTNERS_DICT)
    await event.respond("✅ Berhasil ditambah!")

@bot.on(events.NewMessage(pattern=r'(?i)^/delpartner(.*)'))
async def del_partner(event):
    global PARTNERS_DICT
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    inp = event.pattern_match.group(1).strip()
    if not inp: return
    keys = list(PARTNERS_DICT.keys())
    if inp.isdigit():
        idx = int(inp) - 1
        if 0 <= idx < len(keys):
            del PARTNERS_DICT[keys[idx]]
            save_partners(PARTNERS_DICT)
            await event.respond("🗑️ Dihapus!")
    else:
        if inp in PARTNERS_DICT:
            del PARTNERS_DICT[inp]
            save_partners(PARTNERS_DICT)
            await event.respond("🗑️ Dihapus!")

@bot.on(events.NewMessage(pattern=r'(?i)^/listpartner'))
async def list_partner(event):
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    if not PARTNERS_DICT: return await event.respond("📂 Kosong!")
    txt = "📋 **PARTNER AKTIF:**\n"
    for i, (l, n) in enumerate(PARTNERS_DICT.items(), start=1): txt += f"{i}. {n.upper()} - {l}\n"
    await event.respond(txt, link_preview=False)

async def process_queue():
    global is_processing
    is_processing = True
    while not tagall_queue.empty():
        task = await tagall_queue.get()
        pemicu, teks, mitra, nama_pt, nama, user = task['p'], task['t'], task['m'], task['pt'], task['n'], task['u']
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
        
        w_start = datetime.now().strftime("%H:%M:%S WIB")
        log_start = build_log_start(nama, user, pemicu, w_start, mitra, teks)
        try:
            await bot.send_message(LOG_GROUP_ID, log_start, parse_mode='md', link_preview=False)
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
            selisih = int(time.time() - t_start)
            if selisih not in range(0, 300):
                w_habis = True
                break
            try:
                m_tag = await bot.send_message(TARGET_GROUP_ID, f"{teks}\n\n" + " ".join(chunk), parse_mode='md')
                ids.append(m_tag.id)
            except: pass
            await asyncio.sleep(3.5)
            if selisih not in range(0, 60) and not l_sent:
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

        w_end = datetime.now().strftime("%H:%M:%S WIB")
        log_done = build_log_done(nama, mitra, t_txt, w_end, teks)
        try:
            await bot.send_message(LOG_GROUP_ID, log_done, parse_mode='md', link_preview=False)
        except: pass

        t_now = datetime.now().strftime('%d-%m-%Y %H:%M')
        struk = build_struk(t_now, chat.title, nama_pt, mitra, len(mentions), d_txt)
        try:
            await bot.send_message(pemicu, struk, parse_mode='md', link_preview=False)
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
    v_link, v_name = "", ""
    for url in urls:
        clean = url.strip().rstrip(".,;)")
        if clean in PARTNERS_DICT:
            v_link = clean
            v_name = PARTNERS_DICT[clean]
            break
    if not v_link: return await event.respond("❌ Link tidak terdaftar!")
    s = await event.get_sender()
    n = s.first_name if s.first_name else "User"
    u = s.username if s.username else "tidak_ada"
    q_idx = tagall_queue.qsize()
    await tagall_queue.put({'p': event.sender_id, 't': event.text, 'm': v_link, 'pt': v_name, 'n': n, 'u': u})
    if is_processing: await event.respond(f"⏳ Masuk antrian ke-{q_idx + 1}!")
    else:
        await event.respond("✅ Terverifikasi! Memulai bot...")
        asyncio.create_task(process_queue())

bot.run_until_disconnected()


