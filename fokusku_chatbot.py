import os
import uuid
import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# ─── Konfigurasi halaman ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="FokusKu - Chatbot Konsultan Produktivitas",
    page_icon="🎓",
    layout="wide",
)

# ─── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background-color: #0f1117; }

.hero {
    background: linear-gradient(135deg, #1a1f2e 0%, #16213e 50%, #0d1b2a 100%);
    border: 1px solid #2a3550;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
}
.hero h1 {
    font-family: 'Sora', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.5px;
}
.hero p { color: #64748b; font-size: 0.9rem; margin: 0; }
.accent { color: #3b82f6; }

.waktu-label {
    font-family: 'Sora', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #3b82f6;
    background: #1e3a5f22;
    border: 1px solid #1e3a5f;
    border-radius: 6px;
    padding: 0.2rem 0.7rem;
    display: inline-block;
    margin-bottom: 0.8rem;
}

.aktivitas-card {
    background: #1a1f2e;
    border: 1px solid #2a3550;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 0.85rem;
    color: #94a3b8;
}
.aktivitas-card .nama { color: #e2e8f0; font-weight: 600; flex: 1; }

.badge { padding: 0.15rem 0.6rem; border-radius: 99px; font-size: 0.7rem; font-weight: 600; }
.badge-kelas     { background:#1e3a5f; color:#60a5fa; }
.badge-istirahat { background:#14352a; color:#34d399; }
.badge-sosial    { background:#2d1f3f; color:#a78bfa; }

.greeting-bubble {
    background: #1a1f2e;
    border: 1px solid #2a3550;
    border-left: 3px solid #a78bfa;
    border-radius: 12px;
    padding: 1rem 1.4rem;
    color: #cbd5e1;
    font-size: 0.88rem;
    line-height: 1.7;
    margin-bottom: 1.2rem;
    display: flex;
    gap: 0.8rem;
    align-items: flex-start;
}
.greeting-avatar { font-size: 1.5rem; flex-shrink: 0; margin-top: 0.1rem; }
.greeting-text { flex: 1; }
.greeting-text strong { color: #a78bfa; }

.ai-bubble {
    background: #1a1f2e;
    border: 1px solid #2a3550;
    border-left: 3px solid #3b82f6;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    color: #cbd5e1;
    font-size: 0.88rem;
    line-height: 1.7;
    margin-bottom: 0.8rem;
}
.user-bubble {
    background: #0f2744;
    border: 1px solid #1e3a5f;
    border-left: 3px solid #60a5fa;
    border-radius: 12px;
    padding: 1rem 1.4rem;
    color: #e2e8f0;
    font-size: 0.88rem;
    line-height: 1.7;
    margin-bottom: 0.8rem;
}
.chat-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
    color: #475569;
}

.stButton > button {
    background: #3b82f6 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

.stTextInput input, .stSelectbox select, .stNumberInput input {
    background: #1a1f2e !important;
    border: 1px solid #2a3550 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
.stSelectbox [data-baseweb="select"] > div {
    background: #1a1f2e !important;
    border: 1px solid #2a3550 !important;
}
hr { border-color: #2a3550 !important; }
</style>
""", unsafe_allow_html=True)

# ─── Konstanta ────────────────────────────────────────────────────────────────
WAKTU_LIST = ["🌅 Pagi", "☀️ Siang", "🌇 Sore", "🌙 Malam"]
JENIS_LIST = ["Kelas/Tugas", "Istirahat/Kebugaran", "Sosial/Keagamaan"]
BADGE_CLASS = {
    "Kelas/Tugas":        "badge-kelas",
    "Istirahat/Kebugaran":"badge-istirahat",
    "Sosial/Keagamaan":   "badge-sosial",
}

SYSTEM_PROMPT = """Anda adalah seorang konsultan produktivitas akademik senior.
Analisis list-list data aktivitas mahasiswa di bawah ini.

Jika ada kategori kegiatan Kelas/Tugas atau Sosial/Keagamaan dengan durasi lama namun level fokus rendah (1–2), identifikasi sebagai kebocoran waktu.

Berikan respons dengan struktur berikut:
1. **Ringkasan Harian** – gambaran umum pola waktu hari ini
2. **Analisis Kebocoran Waktu** – aktivitas dengan fokus rendah yang membuang potensi
3. **Rekomendasi Taktis per Aktivitas** – saran konkret untuk setiap aktivitas yang perlu diperbaiki
4. **Skor Produktivitas Hari Ini** – nilai 1–100 beserta justifikasi singkat

Gunakan bahasa Indonesia yang tegas, langsung, dan memotivasi. Hindari basa-basi.

Setelah analisis awal, kamu juga siap menjawab pertanyaan lanjutan dari pengguna terkait hasil analisis ini."""

# ─── Session state init ───────────────────────────────────────────────────────
for key, default in {
    "api_key": "",
    "aktivitas": [],       # list of dict, tiap item punya field "id" unik
    "analisis_result": "",
    "chat_history": [],    # list of {"role": "ai"|"user", "content": str}
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── API Key gate ─────────────────────────────────────────────────────────────
if st.session_state["api_key"] == "":
    st.markdown("""
    <div class="hero">
        <h1>🎓 <span class="accent">FokusKu</span></h1>
        <p>Konsultan produktivitas berbasis AI untuk mahasiswa</p>
    </div>
    """, unsafe_allow_html=True)
    api_key_input = st.text_input("Google Gemini API Key", type="password",
                                   placeholder="Masukkan API key Anda...")
    if st.button("Masuk →"):
        if api_key_input.strip():
            st.session_state["api_key"] = api_key_input.strip()
            st.rerun()
        else:
            st.error("API key tidak boleh kosong.")
    st.stop()

os.environ["GOOGLE_API_KEY"] = st.session_state["api_key"]
client = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🎓 <span class="accent">FokusKu</span></h1>
    <p>Input aktivitas harianmu → AI analisis kebocoran waktu & beri rekomendasi taktis</p>
</div>
""", unsafe_allow_html=True)

# ─── Layout ───────────────────────────────────────────────────────────────────
col_input, col_list = st.columns([1, 1.5], gap="large")

# ══════════════════════════════════════════════════════════════════════════════
# KOLOM KIRI – Form input aktivitas
# ══════════════════════════════════════════════════════════════════════════════
with col_input:
    st.markdown("### Tambah Aktivitas")

    waktu = st.selectbox("Waktu", WAKTU_LIST, key="sel_waktu")
    nama  = st.text_input("Nama Kegiatan", placeholder="Contoh: Kuliah Aljabar Linear")
    jenis = st.selectbox("Jenis Kegiatan", JENIS_LIST, key="sel_jenis")
    durasi = st.number_input("Durasi (menit)", min_value=5, max_value=480, value=60, step=5)
    fokus  = st.selectbox(
        "Level Fokus (1 = sangat rendah, 5 = sangat tinggi)",
        [1, 2, 3, 4, 5], index=2, key="sel_fokus",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("➕ Tambah"):
            if nama.strip():
                st.session_state["aktivitas"].append({
                    "id":     str(uuid.uuid4()),
                    "waktu":  waktu,
                    "nama":   nama.strip(),
                    "jenis":  jenis,
                    "durasi": durasi,
                    "fokus":  fokus,
                })
                # Reset analisis & chat saat data berubah
                st.session_state["analisis_result"] = ""
                st.session_state["chat_history"] = []
                st.rerun()
            else:
                st.warning("Nama kegiatan wajib diisi.")
    with col_b:
        if st.button("🗑 Reset Semua"):
            st.session_state["aktivitas"] = []
            st.session_state["analisis_result"] = ""
            st.session_state["chat_history"] = []
            st.rerun()

    st.divider()

    # Tombol analisis
    if st.session_state["aktivitas"]:
        if st.button("🔍 Analisis Produktivitas →", use_container_width=True):
            lines = [
                f"- [{a['waktu']}] {a['nama']} | Jenis: {a['jenis']} | "
                f"Durasi: {a['durasi']} menit | Level Fokus: {a['fokus']}/5"
                for a in st.session_state["aktivitas"]
            ]
            user_msg = "Berikut daftar aktivitas saya hari ini:\n\n" + "\n".join(lines)

            messages = [SystemMessage(SYSTEM_PROMPT), HumanMessage(user_msg)]
            with st.spinner("AI sedang menganalisis..."):
                try:
                    response = client.invoke(messages)
                    result = response.content
                    st.session_state["analisis_result"] = result
                    # Simpan ke chat_history sebagai konteks awal
                    st.session_state["chat_history"] = [
                        {"role": "user", "content": user_msg},
                        {"role": "ai",   "content": result},
                    ]
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal memanggil AI: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# KOLOM KANAN – Daftar aktivitas + analisis + chat lanjutan
# ══════════════════════════════════════════════════════════════════════════════
with col_list:
    st.markdown("### Daftar Aktivitas Hari Ini")

    # Sapaan konsultan
    st.markdown("""
    <div class="greeting-bubble">
        <div class="greeting-avatar">🤖</div>
        <div class="greeting-text">
            <strong>Halo! Aku konsultan produktivitasmu.</strong><br>
            Tolong isikan daftar kegiatanmu hari ini — mulai dari pagi sampai malam —
            sebelum aku mulai menganalisis dan memberikan rekomendasi ya.
            Semakin lengkap datanya, semakin tajam analisisnya! 💪
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state["aktivitas"]:
        st.info("Belum ada aktivitas. Tambahkan dari panel kiri.")
    else:
        # Kelompokkan per slot waktu
        for waktu_slot in WAKTU_LIST:
            items = [a for a in st.session_state["aktivitas"] if a["waktu"] == waktu_slot]
            if not items:
                continue
            st.markdown(f'<div class="waktu-label">{waktu_slot}</div>', unsafe_allow_html=True)
            for a in items:
                badge_cls = BADGE_CLASS.get(a["jenis"], "badge-kelas")
                fokus_bar = "🟦" * a["fokus"] + "⬜" * (5 - a["fokus"])
                cols = st.columns([6, 1])
                with cols[0]:
                    st.markdown(f"""
                    <div class="aktivitas-card">
                        <div class="nama">{a['nama']}</div>
                        <span class="badge {badge_cls}">{a['jenis']}</span>
                        <span>{a['durasi']}m</span>
                        <span title="Fokus">{fokus_bar}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with cols[1]:
                    # Gunakan UUID sebagai key → tidak konflik walau nama sama
                    if st.button("✕", key=f"del_{a['id']}"):
                        st.session_state["aktivitas"] = [
                            x for x in st.session_state["aktivitas"] if x["id"] != a["id"]
                        ]
                        st.session_state["analisis_result"] = ""
                        st.session_state["chat_history"] = []
                        st.rerun()

        # Statistik ringkas
        total_menit     = sum(a["durasi"] for a in st.session_state["aktivitas"])
        total_aktivitas = len(st.session_state["aktivitas"])
        c1, c2 = st.columns(2)
        c1.metric("Total Aktivitas", total_aktivitas)
        c2.metric("Total Waktu", f"{total_menit} menit")

    # ── Hasil analisis & chat lanjutan ────────────────────────────────────────
    if st.session_state["analisis_result"]:
        st.divider()
        st.markdown("### Analisis AI")

        # Render seluruh riwayat chat (analisis awal + tanya-jawab lanjutan)
        for msg in st.session_state["chat_history"]:
            if msg["role"] == "ai":
                st.markdown('<div class="chat-label">🤖 FokusKu</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="ai-bubble">{msg["content"].replace(chr(10), "<br>")}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="chat-label">🧑 Kamu</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="user-bubble">{msg["content"].replace(chr(10), "<br>")}</div>',
                    unsafe_allow_html=True,
                )

        # Input chat lanjutan
        st.divider()
        st.markdown("#### Tanya lebih lanjut")
        follow_up = st.chat_input("Tanya sesuatu tentang hasil analisis...")
        if follow_up:
            st.session_state["chat_history"].append({"role": "user", "content": follow_up})

            # Bangun ulang messages lengkap untuk konteks
            messages = [SystemMessage(SYSTEM_PROMPT)]
            for msg in st.session_state["chat_history"]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(msg["content"]))
                else:
                    messages.append(AIMessage(msg["content"]))

            with st.spinner("Memproses pertanyaanmu..."):
                try:
                    response = client.invoke(messages)
                    st.session_state["chat_history"].append(
                        {"role": "ai", "content": response.content}
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal memanggil AI: {e}")