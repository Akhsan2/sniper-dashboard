import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pandas_ta as ta
import ccxt
import time
from datetime import datetime

# Konfigurasi Tampilan Halaman Website
st.set_page_config(page_title="Sniper Scalping Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.title("🏹 SNIPER SCALPING CRYPTO DASHBOARD")
st.subheader("Kombinasi Live Chart TradingView & Bot Auto-Screening EMA 9/21 + QQE")

# === SIDEBAR & KONFIGURASI ===
st.sidebar.header("Pengaturan Bot")
COINS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
selected_coin = st.sidebar.selectbox("Pilih Koin Utama untuk Grafik:", COINS)

# Inisialisasi Exchange Bybit via CCXT
exchange = ccxt.bybit({'enableRateLimit': True})

# === TAMPILAN UTAMA (BAGIAN ATAS) ===
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"### 📊 Live Chart: {selected_coin}")
    # Mengubah format koin dari BTC/USDT menjadi BYBIT:BTCUSDT untuk TradingView
    tv_symbol = f"BYBIT:{selected_coin.replace('/', '')}"
    
    # Widget HTML TradingView Embed
    tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:450px;">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "width": "100%",
        "height": 450,
        "symbol": "{tv_symbol}",
        "interval": "15",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "id",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "hide_side_toolbar": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(tradingview_html, height=460)

with col2:
    st.markdown("### 💻 Terminal Bot Scanner (Live Log)")
    
    # Simulasi Terminal Log di Website
    log_placeholder = st.empty()
    log_text = f"[{datetime.now().strftime('%H:%M:%S')}] Memulai sistem Sniper Bot...\n"
    log_text += f"[{datetime.now().strftime('%H:%M:%S')}] Menghubungkan ke API Bybit...\n"
    log_text += f"[{datetime.now().strftime('%H:%M:%S')}] Auto-Screening aktif pada koin: {', '.join(COINS)}\n"
    
    log_placeholder.text_area("Terminal Output", value=log_text, height=400, max_chars=None, key="terminal_log")

# === ENGINE DETEKSI INDIKATOR & REKOMENDASI (BAGIAN BAWAH) ===
st.markdown("---")
st.markdown("### 🎯 KOTAK REKOMENDASI TEMUAN SNIPER SCALPING")

# Fungsi untuk mengambil data dan hitung indikator sniper
def get_signal(symbol):
    try:
        raw_data = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=100)
        df = pd.DataFrame(raw_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['close'] = df['close'].astype(float)
        
        # Hitung EMA Sniper
        df['ema_9'] = ta.ema(df['close'], length=9)
        df['ema_21'] = ta.ema(df['close'], length=21)
        
        # Hitung QQE
        qqe = ta.qqe(df['close'])
        df['qqe_line'], df['qqe_signal'] = qqe.iloc[:, 0], qqe.iloc[:, 1]
        
        # Ambil baris terakhir yang sudah close
        price = df['close'].iloc[-2]
        ema9_now, ema21_now = df['ema_9'].iloc[-2], df['ema_21'].iloc[-2]
        ema9_prev, ema21_prev = df['ema_9'].iloc[-3], df['ema_21'].iloc[-3]
        qqe_line_now, qqe_sig_now = df['qqe_line'].iloc[-2], df['qqe_signal'].iloc[-2]
        
        # Cek Persilangan (Crossover)
        ema_bullish_cross = (ema9_prev < ema21_prev) and (ema9_now > ema21_now)
        ema_bearish_cross = (ema9_prev > ema21_prev) and (ema9_now < ema21_now)
        
        if ema_bullish_cross and qqe_line_now > qqe_sig_now:
            risk = price - ema21_now if (price - ema21_now) > 0 else price * 0.005
            return "BUY / LONG", price, price + risk, price + (risk*2), price + (risk*5), price - risk
        elif ema_bearish_cross and qqe_line_now < qqe_sig_now:
            risk = ema21_now - price if (ema21_now - price) > 0 else price * 0.005
            return "SELL / SHORT", price, price - risk, price - (risk*2), price - (risk*5), price + risk
            
        return "WAIT / SCANNED", price, 0, 0, 0, 0
    except:
        return "ERROR", 0, 0, 0, 0, 0

# Tampilkan Kotak Rekomendasi berdampingan untuk semua koin hasil screening
rec_cols = st.columns(len(COINS))

for i, coin in enumerate(COINS):
    with rec_cols[i]:
        signal, entry, tp1, tp2, tp5, sl = get_signal(coin)
        
        # Beri warna visual berdasarkan status rekomendasi
        if signal == "BUY / LONG":
            st.success(f"🟢 **{coin}**\n\n**STATUS:** {signal}\n\n**Entry:** ${entry:,.3f}\n\n**TP 1 (1:1):** ${tp1:,.3f}\n\n**TP 2 (1:2):** ${tp2:,.3f}\n\n**TP 3 (1:5):** ${tp5:,.3f}\n\n**SL:** ${sl:,.3f}")
        elif signal == "SELL / SHORT":
            st.error(f"🔴 **{coin}**\n\n**STATUS:** {signal}\n\n**Entry:** ${entry:,.3f}\n\n**TP 1 (1:1):** ${tp1:,.3f}\n\n**TP 2 (1:2):** ${tp2:,.3f}\n\n**TP 3 (1:5):** ${tp5:,.3f}\n\n**SL:** ${sl:,.3f}")
        else:
            st.info(f"🟡 **{coin}**\n\n**STATUS:** {signal}\n\nBelum ada persilangan EMA 9/21 Sniper yang valid pada timeframe 15m.")

st.button("🔄 Segarkan Data Website (Refresh)")
st.caption("Catatan: Klik tombol refresh atau ganti koin untuk memperbarui kondisi indikator live.")
