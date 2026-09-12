import os
import asyncio
import time
import json
import re
from telethon import TelegramClient, events

# 1. MENGAMBIL DATA DARI ENVIRONMENT VARIABLES RAILWAY
try:
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    OWNER_ID = int(os.environ.get("OWNER_ID"))
    TARGET_GROUP_ID = int(os.environ.get("TARGET_GROUP_ID"))
except (TypeError, ValueError):
    print("❌ ERROR: Pastikan semua variabel sudah diisi dengan benar di Railway!")
    exit(1)

# Inisialisasi Bot Resmi
bot = TelegramClient('bot_official_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

FILE_DB = "partners_database.json"

def load_partners():
    if os.path.exists(FILE_DB):
        try:
            with open(FILE_DB, "r") as f: return json.load(f)
        except: return []
    return []

def save_partners(data):
    with open(FILE_DB, "w") as f: json.dump(data, f, indent=4)

PARTNERS_LIST = load_partners()
print("⚡ Bot Resmi Auto-Tagall (Public Open + Auto Clean 5m) Siap!")

# --- FITUR 1: TAMBAH PARTNER VIA PM (KHUSUS OWNER) ---
@bot.on(events.NewMessage(pattern=r'(?i)^/addpartner(.*)'))
async def add_partner(event):
    global PARTNERS_LIST
    if event.sender_id != OWNER_ID or not event.is_private: return
    link_baru = event.pattern_match.group(1).strip()
    if not link_baru or not link_baru.startswith(("http://", "https://", "t.me/")):
        await event.respond("⚠️ Format salah! Gunakan:\n`/addpartner https://t.me`")
        return
    if link_baru in PARTNERS_LIST:
        await event.respond("⚠️ Link sudah terdaftar.")
        return
    PARTNERS_LIST.append(link_baru)
    save_partners(PARTNERS_LIST)
    await event.respond(f"✅ Partner Ditambahkan! Total: {len(PARTNERS_LIST)}")

# --- FITUR 2: HAPUS PARTNER VIA PM (KHUSUS OWNER) ---
@bot.on(events.NewMessage(pattern=r'(?i)^/delpartner(.*)'))
async def del_partner(event):
    global PARTNERS_LIST
    if event.sender_id != OWNER_ID or not event.is_private: return
    input_admin = event.pattern_match.group(1).strip()
    if not input_admin: return

    if input_admin.isdigit():
        indeks = int(input_admin) - 1
        if 0 <= indeks < len(PARTNERS_LIST):
            terhapus = PARTNERS_LIST.pop(indeks)
            save_partners(PARTNERS_LIST)
            await event.respond(f"🗑️ Partner nomor {input_admin} ({terhapus}) telah dihapus.")
    else:
        if input_admin in PARTNERS_LIST:
            PARTNERS_LIST.remove(input_admin)
            save_partners(PARTNERS_LIST)
            await event.respond(f"🗑️ Link {input_admin} telah dihapus.")

# --- FITUR 3: LIHAT DAFTAR PARTNER VIA PM (KHUSUS OWNER) ---
@bot.on(events.NewMessage(pattern=r'(?i)^/listpartner'))
async def list_partner(event):
    if event.sender_id != OWNER_ID or not event.is_private: return
    if not PARTNERS_LIST:
        await event.respond("📂 Database Kosong.")
        return
    teks_list = "📋 **DAFTAR PARTNER AKTIF**\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, link in enumerate(PARTNERS_LIST, start=1): teks_list += f"{i}. {link}\n"
    await event.respond(teks_list, link_preview=False)

# --- FITUR 4: PM TEKS UTAMA (BISA OLEH SIAPA PUN / PUBLIC) -> AUTO TAGALL ---
@bot.on(events.NewMessage(incoming=True))
async def handle_public_auto_tagall(event):
    if not event.is_private or event.text.startswith("/"):
        return

    user_pemicu = event.sender_id

    # Pindai tautan di dalam teks promosi
    urls = re.findall(r'(https?://\S+|t\.me/\S+)', event.text)
    if not urls:
        await event.respond("❌ Pesan ditolak! Teks tidak mengandung tautan partner.")
        return

    link_ditemukan = False
    for url in urls:
        clean_url = url.strip().rstrip(".,;)")
        if clean_url in PARTNERS_LIST:
            link_ditemukan = True
            break
            
    if not link_ditemukan:
        await event.respond("❌ **PROSES DITOLAK!** Link Partner di dalam teks ini tidak terdaftar di sistem.")
        return

    await event.respond("✅ **LINK TERVERIFIKASI!** 🚀 Memulai proses Tagall di grup target...")

    # Array untuk menampung semua ID pesan yang dikirim bot di grup agar bisa dihapus massal nanti
    sent_message_ids = []

    try:
        chat = await bot.get_entity(TARGET_GROUP_ID)
        init_msg = await bot.send_message(
            TARGET_GROUP_ID, 
            f"🚀 **TAGALL DIMULAI AUTOMATICALLY BY BOT**\n👥 **GROUP :** **{chat.title}**\n⏱️ *Durasi Maksimal: 5 Menit & Auto-Clean Aktif!*", 
            link_preview=False
        )
        sent_message_ids.append(init_msg.id)
    except Exception as e:
        await event.respond(f"❌ Bot gagal mengirim pesan ke grup target. Pastikan bot sudah masuk dan menjadi Admin!\nError: {e}")
        return

    # Kumpulkan data member grup
    mentions = []
    async for user in bot.iter_participants(TARGET_GROUP_ID):
        if not user.bot:
            name = user.first_name if user.first_name else "Members"
            mentions.append(f"[{name}](tg://user?id={user.id})")

    if not mentions: 
        return

    chunk_size = 5
    chunks = [mentions[i:i + chunk_size] for i in range(0, len(mentions), chunk_size)]
    
    start_time = time.time()
    laporan_terkirim = False
    waktu_habis = False

    # Proses pengiriman mention oleh Bot
    for chunk in chunks:
        # Cek jika durasi total berjalan sudah lewat dari 5 menit (300 detik)
        if time.time() - start_time >= 300:
            waktu_habis = True
            break

        teks_tag = f"{event.text}\n\n📢 **OPIUM TAGALL**\n⭐ **SVBLVNE X DRAGSPIN** ⭐\n━━━━━━━━━━━━━━━━━━━━\n🔗 {', '.join(chunk)}"
        try:
            msg = await bot.send_message(TARGET_GROUP_ID, teks_tag, parse_mode='md')
            sent_message_ids.append(msg.id)
        except:
            pass
        
        await asyncio.sleep(3.5) # Jeda aman anti-flood

        # Kirim bukti status 1 menit ke PM user yang memicu
        if time.time() - start_time >= 60 and not laporan_terkirim:
            try:
                await bot.send_message(user_pemicu, "📊 **LAPORAN PROGRES AUTO-TAGALL**\n✅ Bot sukses berjalan selama 1 menit di grup.")
                laporan_terkirim = True
            except:
                pass

    # Mengirim status akhir ke grup sebelum dibersihkan
    if waktu_habis:
        status_msg = await bot.send_message(TARGET_GROUP_ID, "⏱️ **Batas waktu 5 menit tercapai!** Proses mention dihentikan. Semua pesan sampah akan dihapus otomatis dalam 5 menit dari sekarang...")
    else:
        status_msg = await bot.send_message(TARGET_GROUP_ID, "✅ **Tagall Selesai!** Semua pesan sampah akan dihapus otomatis dalam 5 menit dari sekarang...")
    
    sent_message_ids.append(status_msg.id)
    await event.respond("✅ **Tagall Selesai/Dihentikan!** Mengaktifkan hitung mundur 5 menit untuk penghapusan sampah di grup.")

    # --- SISTEM PENGHAPUSAN OTOMATIS (DELAY 5 MENIT = 300 DETIK) ---
    await asyncio.sleep(300)
    
    try:
        # Menghapus seluruh pesan yang tercatat di array sent_message_ids sekaligus
        await bot.delete_messages(TARGET_GROUP_ID, sent_message_ids)
        # Kirim notifikasi log sukses ke PM Owner agar terpantau bersih
        await bot.send_message(OWNER_ID, f"🧹 **AUTO CLEAN BERHASIL:** Sebanyak {len(sent_message_ids)} pesan sampah tagall di grup tujuan telah dibersihkan tanpa sisa!")
    except Exception as e:
        print(f"Gagal melakukan auto-clean pesan grup: {e}")

bot.run_until_disconnected()

