import os, asyncio, time, json, re, random
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError

try:
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    OWNER_ID = int(os.environ.get("OWNER_ID"))
    TARGET_GROUP_ID = int(os.environ.get("TARGET_GROUP_ID"))
    LOG_GROUP_ID = int(os.environ.get("LOG_GROUP_ID"))
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "admin")
except (TypeError, ValueError):
    print("❌ ERROR: Periksa kembali variabel di Railway!")
    exit(1)

bot = TelegramClient('bot_official_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
FILE_DB = "partners_database.json"
tagall_queue = asyncio.Queue()
is_processing = False
stop_current_tagall = False

EMOJIS = ["👑","🔥","⭐","🚀","💎","✨","🎯","⚡","🔮","🍕","🍃","🪐","🎈","🎉","🎐","🍭","👾","🧸","🦊","🐼","🐸","🦄","🍀","🍒","🍇","🥑","🎀","🔑","🛡️","🧬","🛸","🍿","🎵","🎸","🎲","🎰","🗽","🗼","🏰","🌊"]

def build_log_start(a, b, c, d, e, f):
    clean_f = f.replace('\n', '\n>')
    res = f">📝 **Tagall Dimulai**\n>━━━━━━━━━━━━━━━━━━━━\n>👤 **Nama :** {a}\n>🆔 **Username :** @{b}\n>🔢 **ID :** `{c}`\n>⏰ **Jam :** {d}\n>🤝 **Link :** {e}\n>💬 **Pesan :** \n>{clean_f}\n>━━━━━━━━━━━━━━━━━━━━"
    return res

def build_log_done(a, b, c, d, e):
    clean_e = e.replace('\n', '\n>')
    res = f">🟢 **Tagall Selesai**\n>━━━━━━━━━━━━━━━━━━━━\n>👤 **Pengirim :** {a}\n>🤝 **Link :** {b}\n>⏳ **Durasi :** {c}\n>⏰ **Waktu Selesai :** {d}\n>💬 **Pesan :** \n>{clean_e}\n>━━━━━━━━━━━━━━━━━━━━"
    return res

def build_struk(sender_name, partner_name, link, member_count):
    res = (
        "✨ ✅ **Tagall selesai!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Pengirim: {sender_name}\n"
        f"Partner: {partner_name.upper()}\n"
        f"Link: {link}\n"
        f"Member di-tag: {member_count}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📸 **Jangan lupa SS hasil tagall-nya!**"
    )
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

@bot.on(events.NewMessage(pattern=r'(?i)^/start'))
async def start_command(event):
    if not event.is_private: return
    welcome_text = (
        "👋 **Halo! Selamat datang di Bot Tagall Official**\n\n"
        "Silakan pilih menu layanan di bawah ini untuk memulai atau mendapatkan informasi lebih lanjut:"
    )
    buttons = [
        [Button.inline("🚀 Mulai Tagall", data="menu_tagall")],
        [Button.inline("🤝 Minta PT-an (Partner)", data="menu_mitra")],
        [Button.inline("ℹ️ Info Lainnya", data="menu_info")]
    ]
    await event.respond(welcome_text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=r'^menu_.*'))
async def callback_menu(event):
    data = event.data.decode()
    if data == "menu_tagall":
        text = (
            "🚀 **Cara Memulai Tagall:**\n\n"
            "Cukup kirimkan pesan teks yang berisi **Link Partner/Grup** yang sudah terdaftar secara resmi di bot ini.\n\n"
            "Bot akan otomatis memverifikasi link tersebut dan memasukkan pesanan Anda ke dalam antrian."
        )
    elif data == "menu_mitra":
        text = (
            "🤝 **Pengajuan Kemitraan (PT-an):**\n\n"
            "Untuk mendaftarkan grup Anda sebagai partner resmi, silakan hubungi owner bot melalui username di bawah ini:\n\n"
            f"👤 **Owner:** @{OWNER_USERNAME}\n\n"
            "Kirimkan format pendaftaran kepada admin agar link Anda terdata di database sistem."
        )
    elif data == "menu_info":
        text = (
            "ℹ️ **Informasi Bot & Aturan:**\n\n"
            "• Bot ini berjalan otomatis menggunakan sistem antrian (Queue).\n"
            "• Setiap sesi tagall dibatasi durasi maksimal 5 menit demi keamanan grup.\n"
            "• Pesan tagall sampah akan otomatis dibersihkan secara berkala oleh bot."
        )
    await event.edit(text, buttons=[[Button.inline("🔙 Kembali", data="menu_back")]])

@bot.on(events.CallbackQuery(pattern=r'^menu_back$'))
async def callback_back(event):
    welcome_text = (
        "👋 **Halo! Selamat datang di Bot Tagall Official**\n\n"
        "Silakan pilih menu layanan di bawah ini untuk memulai atau mendapatkan informasi lebih lanjut:"
    )
    buttons = [
        [Button.inline("🚀 Mulai Tagall", data="menu_tagall")],
        [Button.inline("🤝 Minta PT-an (Partner)", data="menu_mitra")],
        [Button.inline("ℹ️ Info Lainnya", data="menu_info")]
    ]
    await event.edit(welcome_text, buttons=buttons)

@bot.on(events.NewMessage(pattern=r'(?i)^/addpt(.*)'))
async def add_partner(event):
    global PARTNERS_DICT
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    inp = event.pattern_match.group(1).strip()
    if " - " not in inp: return await event.respond("⚠️ Format salah! Gunakan: /addpt NAMA - LINK")
    nama_grup, link_baru = inp.split(" - ", 1)
    nama_grup, link_baru = nama_grup.strip(), link_baru.strip()
    if not link_baru.startswith(("http", "t.me")): return await event.respond("⚠️ Link tidak valid!")
    if link_baru in PARTNERS_DICT: return await event.respond("⚠️ Sudah ada!")
    PARTNERS_DICT[link_baru] = nama_grup
    save_partners(PARTNERS_DICT)
    await event.respond("✅ Berhasil ditambah!")

@bot.on(events.NewMessage(pattern=r'(?i)^/lpt'))
async def list_partner(event):
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    if not PARTNERS_DICT: return await event.respond("📂 Kosong!")
    txt = "📋 **PARTNER AKTIF:**\n"
    for i, (l, n) in enumerate(PARTNERS_DICT.items(), start=1):
        txt += f"{i}. {n.upper()} - {l}\n"
    
    buttons = [
        [Button.inline("✏️ Edit Partner", data="partner_select_edit")],
        [Button.inline("🗑️ Hapus Partner", data="partner_select_del")]
    ]
    await event.respond(txt, buttons=buttons, link_preview=False)

@bot.on(events.CallbackQuery(pattern=r'^partner_select_(edit|del)$'))
async def callback_select_action(event):
    action = event.data.decode().split('_')[2]
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: 
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    if not PARTNERS_DICT:
        return await event.edit("📂 Kosong!")
    
    txt = f"📋 **PILIH PARTNER UNTUK DI{action.upper()}:**\n\n"
    buttons = []
    for i, (l, n) in enumerate(PARTNERS_DICT.items(), start=1):
        txt += f"{i}. {n.upper()}\n"
        buttons.append([Button.inline(f"{i}. {n.upper()}", data=f"ptact_{action}_{i-1}")])
    buttons.append([Button.inline("🔙 Kembali", data="partner_list_back")])
    await event.edit(txt, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=r'^partner_list_back$'))
async def callback_list_back(event):
    if not PARTNERS_DICT: return await event.edit("📂 Kosong!")
    txt = "📋 **PARTNER AKTIF:**\n"
    for i, (l, n) in enumerate(PARTNERS_DICT.items(), start=1):
        txt += f"{i}. {n.upper()} - {l}\n"
    buttons = [
        [Button.inline("✏️ Edit Partner", data="partner_select_edit")],
        [Button.inline("🗑️ Hapus Partner", data="partner_select_del")]
    ]
    await event.edit(txt, buttons=buttons, link_preview=False)

@bot.on(events.CallbackQuery(pattern=r'^ptact_del_\d+$'))
async def callback_delete_partner(event):
    global PARTNERS_DICT
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: 
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    idx = int(event.data.decode().split('_')[2])
    keys = list(PARTNERS_DICT.keys())
    if 0 <= idx < len(keys):
        removed_name = PARTNERS_DICT[keys[idx]]
        del PARTNERS_DICT[keys[idx]]
        save_partners(PARTNERS_DICT)
        await event.answer(f"🗑️ {removed_name.upper()} Berhasil Dihapus!", alert=True)
        await callback_list_back(event)

@bot.on(events.CallbackQuery(pattern=r'^ptact_edit_\d+$'))
async def callback_edit_options(event):
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: 
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    idx = int(event.data.decode().split('_')[2])
    keys = list(PARTNERS_DICT.keys())
    if 0 <= idx < len(keys):
        link = keys[idx]
        name = PARTNERS_DICT[link]
        txt = f"⚙️ **PENGATURAN PARTNER:**\n\nNama: {name.upper()}\nLink: {link}\n\nPilih bagian yang ingin diubah:"
        buttons = [
            [Button.inline("📝 Ubah Nama", data=f"ptmod_name_{idx}")],
            [Button.inline("🔗 Ubah Link", data=f"ptmod_link_{idx}")],
            [Button.inline("🔙 Kembali", data="partner_select_edit")]
        ]
        await event.edit(txt, buttons=buttons, link_preview=False)

# Menggunakan handler conversation via bot untuk mengubah data
@bot.on(events.CallbackQuery(pattern=r'^ptmod_(name|link)_\d+$'))
async def callback_modify_input(event):
    global PARTNERS_DICT
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: 
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    
    parts = event.data.decode().split('_')
    field = parts[1]
    idx = int(parts[2])
    keys = list(PARTNERS_DICT.keys())
    
    if 0 <= idx < len(keys):
        old_link = keys[idx]
        old_name = PARTNERS_DICT[old_link]
        
        target_chat = event.chat_id
        async with bot.conversation(target_chat, user_id=event.sender_id, timeout=60) as conv:
            if field == "name":
                await conv.send_message(f"📝 Silakan kirimkan **NAMA BARU** untuk partner **{old_name.upper()}**:")
                response = await conv.get_response()
                new_name = response.text.strip()
                if new_name:
                    PARTNERS_DICT[old_link] = new_name
                    save_partners(PARTNERS_DICT)
                    await conv.send_message(f"✅ Nama berhasil diubah menjadi: **{new_name.upper()}**")
            elif field == "link":
                await conv.send_message(f"🔗 Silakan kirimkan **LINK BARU** untuk partner **{old_name.upper()}**:")
                response = await conv.get_response()
                new_link = response.text.strip()
                if new_link.startswith(("http", "t.me")):
                    if new_link in PARTNERS_DICT:
                        await conv.send_message("⚠️ Link tersebut sudah terdaftar!")
                    else:
                        PARTNERS_DICT[new_link] = PARTNERS_DICT.pop(old_link)
                        save_partners(PARTNERS_DICT)
                        await conv.send_message(f"✅ Link berhasil diperbarui!")
                else:
                    await conv.send_message("⚠️ Link tidak valid! Perubahan dibatalkan.")
        
        # Kembali tampilkan daftar utama
        if event.is_private:
            txt = "📋 **PARTNER AKTIF:**\n"
            for i, (l, n) in enumerate(PARTNERS_DICT.items(), start=1):
                txt += f"{i}. {n.upper()} - {l}\n"
            buttons = [
                [Button.inline("✏️ Edit Partner", data="partner_select_edit")],
                [Button.inline("🗑️ Hapus Partner", data="partner_select_del")]
            ]
            await bot.send_message(target_chat, txt, buttons=buttons, link_preview=False)

@bot.on(events.NewMessage(pattern=r'(?i)^/end'))
async def end_tagall(event):
    global stop_current_tagall, is_processing
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    if not is_processing:
        return await event.respond("⚠️ Tidak ada proses tagall yang sedang berjalan.")
    stop_current_tagall = True
    await event.respond("🛑 Menghentikan proses tagall saat ini...")

async def process_queue():
    global is_processing, stop_current_tagall
    is_processing = True
    while not tagall_queue.empty():
        task = await tagall_queue.get()
        pemicu, teks, mitra, nama_pt, nama, user = task['p'], task['t'], task['m'], task['pt'], task['n'], task['u']
        stop_current_tagall = False
        try:
            await bot.send_message(pemicu, "🚀 **GILIRAN ANDA DIMULAI!**")
        except: pass
        first_tag_id = None
        try:
            chat = await bot.get_entity(TARGET_GROUP_ID)
            i_msg = await bot.send_message(TARGET_GROUP_ID, f"🚀 **TAGALL DIMULAI**\n👥 **GROUP:** {chat.title}", link_preview=False)
            ids = [i_msg.id]
            first_tag_id = i_msg.id
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
            
        # OPTIMISASI KECEPATAN: Menaikkan limit mention per pesan dari 5 menjadi 10
        chunks = [mentions[i:i + 10] for i in range(0, len(mentions), 10)]
        t_start = time.time()
        l_sent = False
        w_habis = False
        
        for chunk in chunks:
            if stop_current_tagall:
                break
            selisih = int(time.time() - t_start)
            if selisih not in range(0, 300):
                w_habis = True
                break
            try:
                m_tag = await bot.send_message(TARGET_GROUP_ID, f"{teks}\n\n" + " ".join(chunk), parse_mode='md')
                ids.append(m_tag.id)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                # Coba kirim ulang sekali lagi setelah floodwait selesai
                try:
                    m_tag = await bot.send_message(TARGET_GROUP_ID, f"{teks}\n\n" + " ".join(chunk), parse_mode='md')
                    ids.append(m_tag.id)
                except: pass
            except: pass
            
            # OPTIMISASI JEDA: Mengurangi interval jeda dari 3.5s menjadi 1.2s agar pengiriman jauh lebih kilat tanpa memicu spam limit berlebih
            await asyncio.sleep(1.2)
            
            if selisih not in range(0, 60) and not l_sent:
                try:
                    await bot.send_message(pemicu, "📊 **BERJALAN 1 MENIT!**")
                    l_sent = True
                except: pass
                
        durasi = round((time.time() - t_start) / 60)
        d_txt = f"{durasi}m" if durasi != 0 else f"{round(time.time() - t_start)}s"
        t_txt = "Dihentikan Paksa (/end)" if stop_current_tagall else ("Selesai (Limit 5m)" if w_habis else "Selesai")
        try:
            s_msg = await bot.send_message(TARGET_GROUP_ID, f"✅ **{t_txt}!** Pesan sampah dihapus dalam 5 menit...")
            ids.append(s_msg.id)
        except: pass
        w_end = datetime.now().strftime("%H:%M:%S WIB")
        log_done = build_log_done(nama, mitra, t_txt, w_end, teks)
        try:
            await bot.send_message(LOG_GROUP_ID, log_done, parse_mode='md', link_preview=False)
        except: pass
        clean_group_id = str(TARGET_GROUP_ID).replace('-100', '')
        link_ke_grup_anda = f"https://t.me/c/{clean_group_id}/{first_tag_id}" if first_tag_id else mitra
        struk = build_struk(nama, nama_pt, mitra, len(mentions))
        try:
            await bot.send_message(
                pemicu, 
                struk, 
                parse_mode='md', 
                link_preview=True, 
                buttons=[
                    [Button.url("Lihat Hasil ↗️", url=link_ke_grup_anda)]
                ]
            )
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
    if not urls: return
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
