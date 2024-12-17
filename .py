import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import MetaTrader5 as mt5
import time

# MACD hesaplama fonksiyonu
def compute_MACD(data, short_window=12, long_window=26, signal_window=9):
    # 1. Kısa vadeli ve uzun vadeli EMA hesapla
    short_ema = data['Close'].ewm(span=short_window, min_periods=1).mean()
    long_ema = data['Close'].ewm(span=long_window, min_periods=1).mean()
    
    # 2. MACD hesapla
    MACD = short_ema - long_ema
    
    # 3. MACD'nin 9 günlük EMA'sı (Sinyal Çizgisi)
    signal_line = MACD.ewm(span=signal_window, min_periods=1).mean()
    
    return MACD, signal_line

# MetaTrader 5'e bağlanma
if not mt5.initialize():
    print("MetaTrader 5 bağlantısı kurulamadı")
    quit()

# Canlı tick verisi çekme fonksiyonu
def get_live_tick(symbol):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"{symbol} için veri bulunamadı!")
        return None
    return tick

# Kullanıcı tanımlı sembol
symbol = "NAS100.x"  # Canlı veri için sembol seçin

# MACD hesaplaması için veri saklama
live_data = pd.DataFrame(columns=['time', 'Close'])

# Canlı veri akışı başlatma
print(f"{symbol} sembolü için canlı veri akışı başlatılıyor...")
try:
    previous_macd = None
    previous_signal = None

    while True:
        # Canlı tick verisini çek
        tick = get_live_tick(symbol)
        if tick is None:
            time.sleep(1)
            continue
        
        # Yeni veri ekle
        new_row = {'time': datetime.now(), 'Close': tick.bid}
        live_data = pd.concat([live_data, pd.DataFrame([new_row])], ignore_index=True)
        
        # Yalnızca son 100 veriyi tut
        live_data = live_data.iloc[-100:]
        
        # MACD hesaplama
        live_data['MACD'], live_data['Signal_Line'] = compute_MACD(live_data)
        
        # Son MACD ve sinyal değerleri
        current_macd = live_data['MACD'].iloc[-1]
        current_signal = live_data['Signal_Line'].iloc[-1]

        # Alım ve satım sinyallerini kontrol et
        if previous_macd is not None and previous_signal is not None:
            if previous_macd < previous_signal and current_macd > current_signal:
                print(f"\033[92mAlım Sinyali: {live_data['time'].iloc[-1]} | Fiyat: {live_data['Close'].iloc[-1]:.5f}\033[0m")
            elif previous_macd > previous_signal and current_macd < current_signal:
                print(f"\033[91mSatım Sinyali: {live_data['time'].iloc[-1]} | Fiyat: {live_data['Close'].iloc[-1]:.5f}\033[0m")
        
        # Bir önceki değerleri güncelle
        previous_macd = current_macd
        previous_signal = current_signal

        # MACD bilgilerini yazdır
        print(f"Zaman: {live_data['time'].iloc[-1]} | Fiyat: {live_data['Close'].iloc[-1]:.5f} | MACD: {current_macd:.5f} | Sinyal: {current_signal:.5f}")

        # Bekleme süresi (1 saniye)
        time.sleep(1)

except KeyboardInterrupt:
    print("Canlı veri akışı durduruldu.")
    mt5.shutdown()
