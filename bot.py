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

add_pt_state = {}

EMOJIS = ["👑","🔥","⭐","🚀","💎","✨","🎯","⚡","🔮","🍕","🍃","🪐","🎈","🎉","🎐","🍭","👾","🧸","🦊","🐼","🐸","🦄","🍀","🍒","🍇","🥑","🎀","🔑","🛡️","🧬","🛸","🍿","🎵","🎸","🎲","🎰","🗽","🗼","🏰","🌊"]

# Perbaikan format blockquote (>) agar mirip seperti gambar
def build_log_start(a, b, c, d, e, f):
    clean_f = f.replace('\n', '\n> ')
    res = (
        f"> **USER :** @{b}\n"
        f"> **USER ID :** `{c}`\n"
        f"> **DURASI :** 5m\n"
        f"> **WAKTU :** {d}\n"
        f"> **PARTNER :** {e}\n\n"
        f"> **TEKS TAGALL :**\n"
        f"> {clean_f}"
    )
    return res

def build_log_done(a, b, c, d, e):
    clean_e = e.replace('\n', '\n> ')
    res = (
        f"> **PENGIRIM :** {a}\n"
        f"> **LINK :** {b}\n"
        f"> **STATUS :** {c}\n"
        f"> **WAKTU SELESAI :** {d}\n\n"
        f"> **PESAN TERAKHIR :**\n"
        f"> {clean_e}"
    )
    return res

# Mengubah format struk PM bot agar persis sesuai gambar yang dikirimkan user
def build_struk(sender_name, partner_name, link, member_count, pj1, pj2, bot_name, ch_link):
    res = (
        "✨ ✅ **Tagall selesai!**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Pengirim:  **{sender_name}**\n"
        f"Partner: {partner_name.upper()}\n"
        f"Link: {link}\n"
        f"Member di-tag: {member_count}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📷 **Jangan lupa SS hasil tagall-nya!**"
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

def get_menu_buttons():
    return [
        [Button.inline("🚀 Mulai Tagall", data="menu_tagall")],
        [Button.inline("🤝 Minta PT-an (Partner)", data="menu_mitra")],
        [Button.inline("ℹ️ Info Lainnya", data="menu_info")]
    ]

@bot.on(events.NewMessage(pattern=r'(?i)^/(start|menu)'))
async def start_command(event):
    if not event.is_private: return
    welcome_text = (
        "👋 **Halo! Selamat datang di Bot Tagall Official**\n\n"
        "> Silakan pilih menu layanan di bawah ini untuk memulai atau mendapatkan informasi lebih lanjut:"
    )
    await event.respond(welcome_text, buttons=get_menu_buttons())

@bot.on(events.CallbackQuery(pattern=r'^menu_.*'))
async def callback_menu(event):
    data = event.data.decode()
    if data == "menu_tagall":
        text = (
            "🚀 **Cara Memulai Tagall:**\n\n"
            "> Cukup kirimkan pesan teks yang berisi **Link Partner/Grup** yang sudah terdaftar secara resmi di bot ini.\n"
            ">\n"
            "> Bot akan otomatis memverifikasi link tersebut dan memasukkan pesanan Anda ke dalam antrian."
        )
    elif data == "menu_mitra":
        text = (
            "🤝 **Pengajuan Kemitraan (PT-an):**\n\n"
            "> Untuk mendaftarkan grup Anda sebagai partner resmi, silakan hubungi owner bot melalui username di bawah ini:\n"
            ">\n"
            f"> 👤 **Owner:** @{OWNER_USERNAME}\n"
            ">\n"
            "> Kirimkan format pendaftaran kepada admin agar link Anda terdata di database sistem."
        )
    elif data == "menu_info":
        text = (
            "ℹ️ **Informasi Bot & Aturan:**\n\n"
            "> • Bot ini berjalan otomatis menggunakan sistem antrian (Queue).\n"
            "> • Setiap sesi tagall dibatasi durasi maksimal 5 menit demi keamanan grup.\n"
            "> • Pesan tagall sampah akan otomatis dibersihkan secara berkala oleh bot."
        )
    elif data == "menu_back":
        welcome_text = (
            "👋 **Halo! Selamat datang di Bot Tagall Official**\n\n"
            "> Silakan pilih menu layanan di bawah ini untuk memulai atau mendapatkan informasi lebih lanjut:"
        )
        await event.edit(welcome_text, buttons=get_menu_buttons())
        return
    await event.edit(text, buttons=[[Button.inline("🔙 Kembali", data="menu_back")]])

@bot.on(events.NewMessage(pattern=r'(?i)^/cancel'))
async def cancel_command(event):
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    user_id = event.sender_id
    if user_id in add_pt_state:
        del add_pt_state[user_id]
        await event.respond("❌ **Proses penginputan/pengeditan data partner telah dibatalkan.**")
    else:
        await event.respond("⚠️ Tidak ada proses penginputan partner yang sedang aktif.")

def build_partner_page(page=1):
    keys = list(PARTNERS_DICT.keys())
    total_items = len(keys)
    items_per_page = 10
    total_pages = (total_items + items_per_page - 1) // items_per_page
    if total_pages == 0: total_pages = 1
    
    if page < 1: page = 1
    if page > total_pages: page = total_pages
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_keys = keys[start_idx:end_idx]
    
    if not keys:
        return (
            "📋 **PANEL LAYANAN PARTNER**\n\n> 📂 Status database: Kosong!", 
            [[Button.inline("➕ Tambah PT Baru", data="pt_add_start")], [Button.inline("🔴 Tutup Panel", data="panel_close")]]
        )
    
    txt = (
        "📋 **PANEL LAYANAN PARTNER**\n\n"
        f"> Silakan pilih salah satu partner aktif dari list halaman [{page}/{total_pages}] di bawah ini untuk mengelola data:"
    )
    buttons = []
    
    for i, l in enumerate(page_keys, start=start_idx + 1):
        p_data = PARTNERS_DICT[l]
        n = p_data.get("nama", "Tanpa Nama") if isinstance(p_data, dict) else p_data
        buttons.append([Button.inline(f"{i}. {n.upper()}", data=f"pt_manage_{i-1}")])
        
    nav_row = []
    if page > 1:
        nav_row.append(Button.inline("◀️", data=f"pt_page_{page-1}"))
    else:
        nav_row.append(Button.inline("◀️", data="pt_page_noop"))
        
    nav_row.append(Button.inline(f"[{page}/{total_pages}]", data="pt_page_noop"))
    
    if page < total_pages:
        nav_row.append(Button.inline("▶️", data=f"pt_page_{page+1}"))
    else:
        nav_row.append(Button.inline("▶️", data="pt_page_noop"))
        
    buttons.append(nav_row)
    buttons.append([Button.inline("➕ Tambah PT Baru", data="pt_add_start")])
    buttons.append([Button.inline("🔴 Tutup Panel", data="panel_close")])
    
    return txt, buttons

@bot.on(events.NewMessage(pattern=r'(?i)^/lpt'))
async def list_partner(event):
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    txt, buttons = build_partner_page(1)
    await event.respond(txt, buttons=buttons, link_preview=False)

@bot.on(events.CallbackQuery(pattern=r'^pt_page_.*'))
async def callback_pt_page(event):
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID:
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    parts = event.data.decode().split('_')
    data = parts[2]
    if data == "noop": return await event.answer()
    page = int(data)
    txt, buttons = build_partner_page(page)
    await event.edit(txt, buttons=buttons, link_preview=False)

@bot.on(events.CallbackQuery(pattern=r'^panel_close$'))
async def callback_panel_close(event):
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID:
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    await event.edit("> 🔒 **Panel layanan partner telah ditutup.**", buttons=None)

@bot.on(events.CallbackQuery(pattern=r'^pt_manage_\d+$'))
async def callback_manage_partner(event):
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID:
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    parts = event.data.decode().split('_')
    idx = int(parts[2])
    keys = list(PARTNERS_DICT.keys())
    if 0 <= idx < len(keys):
        l = keys[idx]
        pd = PARTNERS_DICT[l]
        if not isinstance(pd, dict):
            pd = {"nama": pd, "bot": "-", "ch": "-", "pj1": "-", "pj2": "-"}
            
        txt = (
            "⚙️ **PILIH BAGIAN YANG INGIN DIUBAH:**\n\n"
            f"> 🏢 **Nama GC :** {pd.get('nama', '-')}\n"
            f"> 🔗 **Link GC :** {l}\n"
            f"> 🤖 **Nama Bot :** {pd.get('bot', '-')}\n"
            f"> 📢 **Link CH :** {pd.get('ch', '-')}\n"
            f"> 👮 **PJ 1 :** {pd.get('pj1', '-')}\n"
            f"> 👮 **PJ 2 :** {pd.get('pj2', '-')}"
        )
        buttons = [
            [Button.inline("👆 Edit Nama GC", data=f"pt_edit_nama_{idx}"), Button.inline("👆 Edit Link GC", data=f"pt_edit_link_{idx}")],
            [Button.inline("👆 Edit Bot", data=f"pt_edit_bot_{idx}"), Button.inline("👆 Edit CH", data=f"pt_edit_ch_{idx}")],
            [Button.inline("👆 Edit PJ 1", data=f"pt_edit_pj1_{idx}"), Button.inline("👆 Edit PJ 2", data=f"pt_edit_pj2_{idx}")],
            [Button.inline("🔴 Hapus Partner", data=f"pt_delconf_{idx}"), Button.inline("❌ Kembali", data="pt_back_list")],
            [Button.inline("🔴 Tutup Panel", data="panel_close")]
        ]
        await event.edit(txt, buttons=buttons, link_preview=False)

@bot.on(events.CallbackQuery(pattern=r'^pt_back_list$'))
async def callback_pt_back_list(event):
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID:
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    txt, buttons = build_partner_page(1)
    await event.edit(txt, buttons=buttons, link_preview=False)

@bot.on(events.CallbackQuery(pattern=r'^pt_delconf_\d+$'))
async def callback_delconf_partner(event):
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID:
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    parts = event.data.decode().split('_')
    idx = int(parts[2])
    keys = list(PARTNERS_DICT.keys())
    if 0 <= idx < len(keys):
        l = keys[idx]
        p_data = PARTNERS_DICT[l]
        n = p_data.get("nama", p_data) if isinstance(p_data, dict) else p_data
        txt = (
            "⚠️ **KONFIRMASI PENGHAPUSAN**\n\n"
            f"> Apakah Anda yakin ingin menghapus partner '{n.upper()}' dari database secara permanen?"
        )
        buttons = [
            [Button.inline("✅ Ya, Hapus", data=f"pt_delfinal_{idx}")],
            [Button.inline("❌ Batalkan", data=f"pt_manage_{idx}")]
        ]
        await event.edit(txt, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=r'^pt_delfinal_\d+$'))
async def callback_delfinal_partner(event):
    global PARTNERS_DICT
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID:
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    parts = event.data.decode().split('_')
    idx = int(parts[2])
    keys = list(PARTNERS_DICT.keys())
    if 0 <= idx < len(keys):
        removed_name = PARTNERS_DICT[keys[idx]]
        if isinstance(removed_name, dict):
            removed_name = removed_name.get("nama", "Tanpa Nama")
        del PARTNERS_DICT[keys[idx]]
        save_partners(PARTNERS_DICT)
        await event.answer(f"🗑️ {removed_name.upper()} Berhasil Dihapus!", alert=True)
    txt, buttons = build_partner_page(1)
    await event.edit(txt, buttons=buttons, link_preview=False)

@bot.on(events.CallbackQuery(pattern=r'^pt_edit_(nama|link|bot|ch|pj1|pj2)_\d+$'))
async def callback_trigger_edit(event):
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID:
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    parts = event.data.decode().split('_')
    tipe = parts[2]
    idx = int(parts[3])
    
    add_pt_state[event.sender_id] = {"step": f"edit_{tipe}", "idx": idx}
    
    field_labels = {
        'nama': 'Nama Grup (GC) baru',
        'link': 'Link Grup (GC) baru berawalan http/t.me',
        'bot': 'Nama Bot baru',
        'ch': 'Link Channel (CH) baru',
        'pj1': 'Username Penanggung Jawab 1 (PJ 1) baru',
        'pj2': 'Username Penanggung Jawab 2 (PJ 2) baru'
    }
    
    txt = (
        "📝 **MODE EDIT DATA PARTNER**\n\n"
        f"> Silakan kirimkan data **{field_labels[tipe]}** melalui pesan chat untuk memperbarui partner ini.\n"
        f"> _Ketik /cancel jika ingin membatalkan._"
    )
    await event.respond(txt)
    await event.answer()

@bot.on(events.CallbackQuery(pattern=r'^pt_add_start$'))
async def callback_add_start(event):
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID:
        return await event.answer("⚠️ Tidak ada akses!", alert=True)
    add_pt_state[event.sender_id] = {"step": "input_nama"}
    txt = (
        "➕ **TAMBAH PARTNER BARU (TAHAP 1/6)**\n\n"
        "> Silakan masukkan **Nama Partner (PT / Nama GC)**:\n"
        "> _Ketik /cancel jika ingin membatalkan._"
    )
    await event.respond(txt)
    await event.answer()

@bot.on(events.NewMessage(incoming=True))
async def handle_multistep_input(event):
    global PARTNERS_DICT
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    user_id = event.sender_id
    if user_id not in add_pt_state: return
    
    user_text = event.text.strip()
    if user_text.startswith("/cancel"): return
    
    state = add_pt_state[user_id]
    step = state.get("step")
    
    if step == "input_nama":
        state["nama"] = user_text
        state["step"] = "input_link"
        txt = (
            "➕ **TAMBAH PARTNER BARU (TAHAP 2/6)**\n\n"
            "> Masukkan **Link Partner (Link GC)** berawalan http atau t.me:"
        )
        await event.respond(txt)
        
    elif step == "input_link":
        if not user_text.startswith(("http", "t.me")):
            return await event.respond("> ⚠️ Link tidak valid! Harus diawali http atau t.me. Silakan kirim ulang:")
        if user_text in PARTNERS_DICT:
            return await event.respond("> ⚠️ Link tersebut sudah terdaftar! Silakan kirim link lain:")
        state["link"] = user_text
        state["step"] = "input_bot"
        txt = (
            "➕ **TAMBAH PARTNER BARU (TAHAP 3/6)**\n\n"
            "> Masukkan **Nama Bot** pendukung:"
        )
        await event.respond(txt)
        
    elif step == "input_bot":
        state["bot"] = user_text
        state["step"] = "input_ch"
        txt = (
            "➕ **TAMBAH PARTNER BARU (TAHAP 4/6)**\n\n"
            "> Masukkan **Link Channel (CH)**:"
        )
        await event.respond(txt)
        
    elif step == "input_ch":
        state["ch"] = user_text
        state["step"] = "input_pj1"
        txt = (
            "➕ **TAMBAH PARTNER BARU (TAHAP 5/6)**\n\n"
            "> Masukkan Username **Penanggung Jawab 1 (PJ 1)**:"
        )
        await event.respond(txt)
        
    elif step == "input_pj1":
        state["pj1"] = user_text
        state["step"] = "input_pj2"
        txt = (
            "➕ **TAMBAH PARTNER BARU (TAHAP 6/6 - TERAKHIR)**\n\n"
            "> Masukkan Username **Penanggung Jawab 2 (PJ 2)**:"
        )
        await event.respond(txt)
        
    elif step == "input_pj2":
        state["pj2"] = user_text
        
        PARTNERS_DICT[state["link"]] = {
            "nama": state["nama"],
            "bot": state["bot"],
            "ch": state["ch"],
            "pj1": state["pj1"],
            "pj2": state["pj2"]
        }
        save_partners(PARTNERS_DICT)
        del add_pt_state[user_id]
        
        txt_done = (
            "✅ **PARTNER BERHASIL DITAMBAHKAN!**\n\n"
            f"> **Nama GC :** {state['nama']}\n"
            f"> **Link GC :** {state['link']}\n"
            f"> **Bot :** {state['bot']}\n"
            f"> **CH :** {state['ch']}\n"
            f"> **PJ 1 :** {state['pj1']}\n"
            f"> **PJ 2 :** {state['pj2']}\n\n"
            "Silakan panggil kembali `/lpt` untuk melihat list."
        )
        await event.respond(txt_done)

    elif step.startswith("edit_"):
        parts = step.split("_")
        tipe = parts[1]
        idx = state["idx"]
        keys = list(PARTNERS_DICT.keys())
        
        if 0 <= idx < len(keys):
            old_link = keys[idx]
            old_data = PARTNERS_DICT[old_link]
            
            if not isinstance(old_data, dict):
                old_data = {"nama": old_data, "bot": "-", "ch": "-", "pj1": "-", "pj2": "-"}
                
            if tipe == "link":
                if not user_text.startswith(("http", "t.me")):
                    return await event.respond("> ⚠️ Link tidak valid! Harus diawali http atau t.me. Silakan kirim ulang:")
                if user_text != old_link and user_text in PARTNERS_DICT:
                    return await event.respond("> ⚠️ Link tersebut sudah terdaftar! Silakan kirim link lain:")
                del PARTNERS_DICT[old_link]
                PARTNERS_DICT[user_text] = old_data
            else:
                old_data[tipe] = user_text
                PARTNERS_DICT[old_link] = old_data
                
            save_partners(PARTNERS_DICT)
            del add_pt_state[user_id]
            
            txt_success = (
                "✅ **PERUBAHAN BERHASIL DISIMPAN!**\n\n"
                f"> Data **{tipe.upper()}** berhasil dimodifikasi. Silakan panggil ulang perintah `/lpt` untuk melihat pembaruan."
            )
            await event.respond(txt_success)

@bot.on(events.NewMessage(pattern=r'(?i)^/end'))
async def end_tagall(event):
    global stop_current_tagall, is_processing
    if not event.is_private and event.chat_id != LOG_GROUP_ID: return
    if event.sender_id != OWNER_ID and event.chat_id != LOG_GROUP_ID: return
    if not is_processing:
        return await event.respond("> ⚠️ Tidak ada proses tagall yang sedang berjalan.")
    stop_current_tagall = True
    await event.respond("> 🛑 Menghentikan proses tagall saat ini...")

async def process_queue():
    global is_processing, stop_current_tagall
    is_processing = True
    while not tagall_queue.empty():
        task = await tagall_queue.get()
        pemicu, teks, mitra, nama_pt, nama, user = task['p'], task['t'], task['m'], task['pt'], task['n'], task['u']
        v_bot, v_ch, v_pj1, v_pj2 = task['bot'], task['ch'], task['pj1'], task['pj2']
        
        stop_current_tagall = False
        try:
            await bot.send_message(pemicu, "> 🚀 **GILIRAN ANDA DIMULAI!**")
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
            
        w_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
                await asyncio.sleep(e.seconds + 1)
                try:
                    m_tag = await bot.send_message(TARGET_GROUP_ID, f"{teks}\n\n" + " ".join(chunk), parse_mode='md')
                    ids.append(m_tag.id)
                except: pass
            except: pass
            
            await asyncio.sleep(1.2)
            
            if selisih not in range(0, 60) and not l_sent:
                try:
                    await bot.send_message(pemicu, "> 📊 **BERJALAN 1 MENIT!**")
                    l_sent = True
                except: pass
                
        durasi = round((time.time() - t_start) / 60)
        t_txt = "Dihentikan Paksa (/end)" if stop_current_tagall else ("Selesai (Limit 5m)" if w_habis else "Selesai")
        
        try:
            s_msg = await bot.send_message(TARGET_GROUP_ID, f"✅ **{t_txt}!** Pesan sampah dihapus dalam 5 menit...")
            ids.append(s_msg.id)
        except: pass
        
        w_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_done = build_log_done(nama, mitra, t_txt, w_end, teks)
        try:
            await bot.send_message(LOG_GROUP_ID, log_done, parse_mode='md', link_preview=False)
        except: pass
        
        clean_group_id = str(TARGET_GROUP_ID).replace('-100', '')
        link_ke_grup_anda = f"https://t.me/c/{clean_group_id}/{first_tag_id}" if first_tag_id else mitra
        struk = build_struk(nama, nama_pt, mitra, len(mentions), v_pj1, v_pj2, v_bot, v_ch)
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
        await bot.send_message(OWNER_ID, f"> 🧹 **BERSIH:** {len(ids)} pesan dihapus!")
    except: pass

@bot.on(events.NewMessage(incoming=True))
async def handle_public_auto_tagall(event):
    if not event.is_private or event.text.startswith("/"): return
    if event.sender_id in add_pt_state: return
    
    urls = re.findall(r'(https?://\S+|t\.me/\S+)', event.text)
    if not urls: return
    v_link, v_name, v_bot, v_ch, v_pj1, v_pj2 = "", "", "", "", "", ""
    for url in urls:
        clean = url.strip().rstrip(".,;)")
        if clean in PARTNERS_DICT:
            v_link = clean
            pd = PARTNERS_DICT[clean]
            if isinstance(pd, dict):
                v_name = pd.get('nama', 'Tanpa Nama')
                v_bot = pd.get('bot', '-')
                v_ch = pd.get('ch', '-')
                v_pj1 = pd.get('pj1', '-')
                v_pj2 = pd.get('pj2', '-')
            else:
                v_name = pd
                v_bot, v_ch, v_pj1, v_pj2 = "-", "-", "-", "-"
            break
            
    if not v_link:
        return await event.respond(
            "❌ **LINK TIDAK TERDAFTAR**\n\n"
            "> Mohon maaf, link yang Anda kirimkan belum terdata sebagai mitra resmi kami."
        )
        
    s = await event.get_sender()
    n = s.first_name if s.first_name else "User"
    u = s.username if s.username else "tidak_ada"
    q_idx = tagall_queue.qsize()
    
    await tagall_queue.put({
        'p': event.sender_id, 't': event.text, 'm': v_link, 'pt': v_name, 'n': n, 'u': u,
        'bot': v_bot, 'ch': v_ch, 'pj1': v_pj1, 'pj2': v_pj2
    })
    
    if is_processing:
        await event.respond(
            "⏳ **ANTREAN DITERIMA**\n\n"
            f"> Permintaan Anda telah dimasukkan ke dalam barisan antrean nomor ke-{q_idx + 1}."
        )
    else:
        await event.respond(
            "✅ **TERVERIFIKASI!**\n\n"
            "> Link valid! Memulai bot tagall space line..."
        )
        asyncio.create_task(process_queue())

bot.run_until_disconnected()
