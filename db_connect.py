import psycopg2
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import warnings

warnings.filterwarnings('ignore')

try:
    conn = psycopg2.connect(
        dbname="SaglikliOneriDB", 
        user="postgres", 
        password="12345", 
        host="localhost", 
        port="5432"
    )
    cur = conn.cursor()

    cur.execute("SELECT * FROM Besinler;")
    satirlar = cur.fetchall()
    sutun_isimleri = [desc[0] for desc in cur.description] 

    df = pd.DataFrame(satirlar, columns=sutun_isimleri)

    cur.close()
    conn.close()

    sayisal_sutunlar = ['grams', 'calories', 'protein', 'fat', 'sat_fat', 'fiber', 'carbs']

    for sutun in sayisal_sutunlar:
        df[sutun] = df[sutun].replace('t', '0')
        df[sutun] = df[sutun].astype(str).str.replace(',', '')
        df[sutun] = pd.to_numeric(df[sutun], errors='coerce')

    df.fillna(0, inplace=True)

    secilen_indeks = 4 
    secilen_besin_adi = df.iloc[secilen_indeks]['food']
    hedef_kalori = df.iloc[secilen_indeks]['calories']
    hedef_doymus_yag = df.iloc[secilen_indeks]['sat_fat']

    print(f"Seçilen Sağlıksız Besin: {secilen_besin_adi} (Kalori: {hedef_kalori}, Doymuş Yağ: {hedef_doymus_yag})")

    saglikli_df = df[(df['calories'] < hedef_kalori) & (df['sat_fat'] <= hedef_doymus_yag)].copy()
    saglikli_df.reset_index(drop=True, inplace=True)

    ozellikler = ['calories', 'protein', 'fat', 'carbs']
    scaler = StandardScaler()
    
    X_saglikli = scaler.fit_transform(saglikli_df[ozellikler])

    knn_model = NearestNeighbors(n_neighbors=3, metric='euclidean')
    knn_model.fit(X_saglikli)

    hedef_degerler = scaler.transform([df.iloc[secilen_indeks][ozellikler]])
    mesafeler, komsu_indeksleri = knn_model.kneighbors(hedef_degerler)

    print("\n--- AKILLI ÖNERİ SİSTEMİ ÇALIŞIYOR ---")
    print("Buna Benzer Daha SAĞLIKLI Alternatifler:")
    
    oneriler_listesi = []
    for i in range(3):
        komsu_idx = komsu_indeksleri[0][i]
        oneri_besin = saglikli_df.iloc[komsu_idx]['food']
        oneri_kalori = saglikli_df.iloc[komsu_idx]['calories']
        oneriler_listesi.append(oneri_besin)
        print(f"- {oneri_besin} (Kalori: {oneri_kalori})")

    conn_insert = psycopg2.connect(
        dbname="SaglikliOneriDB", 
        user="postgres", 
        password="12345", 
        host="localhost", 
        port="5432"
    )
    cur_insert = conn_insert.cursor()
    
    insert_sorgusu = """
        INSERT INTO Oneriler (secilen_besin, oneri_1, oneri_2, oneri_3) 
        VALUES (%s, %s, %s, %s)
    """
    degerler = (secilen_besin_adi, oneriler_listesi[0], oneriler_listesi[1], oneriler_listesi[2])
    
    cur_insert.execute(insert_sorgusu, degerler)
    conn_insert.commit() 
    
    cur_insert.close()
    conn_insert.close()
    print("\nBAŞARI: Akıllı modelin sonuçları veritabanına kalıcı olarak kaydedildi!")

except Exception as hata:
    print("Bir hata oluştu:", hata)