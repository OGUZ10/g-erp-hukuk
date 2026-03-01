import streamlit as st
import psycopg2
import pandas as pd

# --- 1. VERİTABANI BAĞLANTI FONKSİYONU (En Üstte Olmalı) ---
# --- 1. VERİTABANI BAĞLANTI VE KURULUM FONKSİYONU ---
def get_connection():
    try:
        # Buraya kendi Neon.tech linkini yapıştır
        url = "postgresql://neondb_owner:npg_jC5idmTFc7pX@ep-broad-mud-aiehr9uw-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        conn = psycopg2.connect(url)
        
        # TABLO KONTROLÜ (Eğer yoksa oluşturur)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS finans_hareketleri (
                id SERIAL PRIMARY KEY,
                muvekkil_ad TEXT NOT NULL,
                miktar DECIMAL(15,2) NOT NULL,
                tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        
        return conn
    except Exception as e:
        st.error(f"Bulut bağlantı hatası: {e}")
        return None

# --- 2. GÜVENLİK KONTROLÜ ---
def check_password():
    if "oturum" not in st.session_state:
        st.session_state["oturum"] = False

    if not st.session_state["oturum"]:
        st.title("🔒 G-ERP Güvenli Giriş")
        kullanici = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap"):
            if kullanici == "admin" and sifre == "hukuk123":
                st.session_state["oturum"] = True
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")
        return False
    return True
# --- 3. ANA UYGULAMA ---
if check_password():
    st.sidebar.title("🚀 G-ERP Menü")
    sayfa = st.sidebar.selectbox("Bölüm Seçin", ["📊 Dashboard", "➕ Masraf Girişi", "🚪 Çıkış"])


    if sayfa == "📊 Dashboard":
        st.header("⚖️ Finansal Genel Görünüm")
        conn = get_connection()
        if conn:
            try:
                df = pd.read_sql_query("SELECT * FROM finans_hareketleri ORDER BY id DESC", conn)
                
                if not df.empty:
                    # --- ÜST ÖZET KARTLARI ---
                    toplam_tutar = df['miktar'].sum()
                    islem_sayisi = len(df)
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Toplam Tahsilat/Masraf", f"₺{toplam_tutar:,.2f}")
                    col2.metric("Toplam İşlem Adedi", f"{islem_sayisi} Kayıt")
                    
                    st.divider()
                    
                    # --- VERİ TABLOSU ---
                    st.subheader("Son Hareketler")
                    st.dataframe(df, use_container_width=True)
                    
                    # --- KAYIT SİLME (Opsiyonel) ---
                    with st.expander("🗑️ Kayıt Sil"):
                        silinecek_id = st.number_input("Silmek istediğiniz Kayıt ID'sini girin:", min_value=1, step=1)
                        if st.button("Kaydı Kalıcı Olarak Sil"):
                            cur = conn.cursor()
                            cur.execute("DELETE FROM finans_hareketleri WHERE id = %s", (silinecek_id,))
                            conn.commit()
                            st.warning(f"ID {silinecek_id} olan kayıt silindi. Lütfen sayfayı yenileyin.")
                            st.rerun()
                else:
                    st.info("Henüz veri yok.")
                conn.close()
            except Exception as e:
                st.error(f"Hata: {e}")

    elif sayfa == "➕ Masraf Girişi":
        st.header("📝 Yeni Masraf / Tahsilat Kaydı")
        
        with st.form("yeni_kayit_formu"):
            muvekkil = st.text_input("Müvekkil Adı / Dosya No")
            tutar = st.number_input("İşlem Tutarı (₺)", min_value=0.0, step=10.0)
            islem_notu = st.text_area("İşlem Detayı")
            
            submit = st.form_submit_button("Sisteme Kaydet")
            
            if submit:
                if muvekkil and tutar > 0:
                    conn = get_connection()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO finans_hareketleri (muvekkil_ad, miktar) 
                            VALUES (%s, %s)
                        """, (muvekkil, tutar))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success(f"✅ {muvekkil} için {tutar} TL işlem kaydedildi!")
                else:
                    st.error("Lütfen müvekkil adı ve tutar giriniz.")

    elif sayfa == "🚪 Çıkış":
        st.session_state["oturum"] = False
        st.rerun()
