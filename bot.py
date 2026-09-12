import os
import asyncio
import time
import json
import re
from datetime import datetime
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

# Inisialisasi Antrian Global (Queue)
tagall_queue = asyncio.Queue()
is_processing = False

def load_partners():
    if os.path.exists(FILE_DB):
        try:
            with open(FILE_DB, "r") as f: return json.load(f)
        except: return []
    return []

def save_partners(data):
    with open(FILE_DB, "w") as f: json.dump(data, f, indent=4)

PARTNERS_LIST = load_partners()
print("⚡ Bot Resmi Auto-Tagall Antrian + Laporan Banner Siap!")

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
        if 0 = 300: # Batasan 5 menit
                waktu_habis = True
                break

            teks_tag = f"{pesan_teks}\n\n📢 **OPIUM TAGALL**\n⭐ **SVBLVNE X DRAGSPIN** ⭐\n━━━━━━━━━━━━━━━━━━━━\n🔗 {', '.join(chunk)}"
            try:
                msg = await bot.send_message(TARGET_GROUP_ID, teks_tag, parse_mode='md')
                sent_message_ids.append(msg.id)
                total_tertag += len(chunk)
            except:
                pass
            
            await asyncio.sleep(3.5)

            if time.time() - start_time >= 60 and not laporan_terkirim:
                try:
                    await bot.send_message(user_pemicu, "📊 **LAPORAN PROGRES AUTO-TAGALL**\n✅ Bot sukses berjalan selama 1 menit di grup.")
                    laporan_terkirim = True
                except:
                    pass

        # Menghitung durasi asli pemrosesan
        end_time = time.time()
        durasi_menit = round((end_time - start_time) / 60)
        durasi_teks = f"{durasi_menit}m" if durasi_menit > 0 else f"{round(end_time - start_time)}s"

        # Format Waktu Indonesia Barat (WIB) untuk struk laporan
        waktu_sekarang = datetime.now().strftime("%d-%m-%Y %H:%M")

        if waktu_habis:
            status_msg = await bot.send_message(TARGET_GROUP_ID, "⏱️ **Batas waktu 5 menit tercapai!** Semua pesan sampah akan dibersihkan dalam 5 menit...")
        else:
            status_msg = await bot.send_message(TARGET_GROUP_ID, "✅ **Tagall Selesai!** Semua pesan sampah akan dibersihkan dalam 5 menit...")
        
        sent_message_ids.append(status_msg.id)

        # --- 2. SISTEM STRUK BUKTI LAPORAN DI PM USER ---
        # Mencari banner gambar profil grup untuk dipakai kembali sebagai background laporan (jika ada)
        banner_file = None
        try:
            banner_file = await bot.download_profile_photo(TARGET_GROUP_ID, file=bytes)
        except:
            pass

        # Merakit teks laporan akhir persis seperti gambar contoh
        teks_bukti = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "**TAGALL SELESAI**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📆 **TANGGAL :** `{waktu_sekarang}`\n"
            f"🏰 **GROUP :** **{chat.title}**\n"
            f"🤝 **PARTNER :** {link_mitra}\n"
            f"📩 **TERKIRIM :** `{total_tertag}`\n"
            f"⏳ **DURASI :** `{durasi_teks}`\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "**teruskan pesan ini sebagai bukti!!!**"
        )

        try:
            # Kirim struk bukti beserta gambar banner-nya ke PM user pemicu
            if banner_file:
                await bot.send_file(user_pemicu, file=banner_file, caption=teks_bukti, parse_mode='md')
            else:
                await bot.send_message(user_pemicu, teks_bukti, parse_mode='md', link_preview=False)
        except:
            pass

        # Menandakan pekerjaan ini selesai diproses
        tagall_queue.task_done()

        # Jalankan fungsi pembersihan berkas sampah di background agar tidak mengunci antrean selanjutnya
        asyncio.create_task(clean_messages_delayed(sent_message_ids))

    is_processing = False

# Fungsi internal untuk membersihkan pesan grup setelah delay 5 menit
async def clean_messages_delayed(message_ids):
    await asyncio.sleep(300) # Tunggu 5 menit (300 detik)
    try:
        await bot.delete_messages(TARGET_GROUP_ID, message_ids)
        await bot.send_message(OWNER_ID, f"🧹 **AUTO CLEAN BERHASIL:** Sebanyak {len(message_ids)} pesan sampah tagall di grup target telah dibersihkan tanpa sisa!")
    except Exception as e:
        print(f"Gagal melakukan auto-clean pesan grup: {e}")

# --- FITUR 4: PM TEKS UTAMA (PUBLIC) -> VALIDASI -> MASUKKAN KE ANTRIAN ---
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
    link_terverifikasi = ""
    for url in urls:
        clean_url = url.strip().rstrip(".,;)")
        if clean_url in PARTNERS_LIST:
            link_ditemukan = True
            link_terverifikasi = clean_url
            break
            
    if not link_ditemukan:
        await event.respond("❌ **PROSES DITOLAK!** Link Partner di dalam teks ini tidak terdaftar di sistem.")
        return

