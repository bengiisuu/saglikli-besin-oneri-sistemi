import psycopg2
import pandas as pd
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

    print("--- HAM VERİDEN ÖRNEK ---")
    print(df[['food', 'calories', 'fat']].head())

    
    sayisal_sutunlar = ['grams', 'calories', 'protein', 'fat', 'sat_fat', 'fiber', 'carbs']

    for sutun in sayisal_sutunlar:
        df[sutun] = df[sutun].replace('t', '0')
        
        df[sutun] = df[sutun].astype(str).str.replace(',', '')
        
        df[sutun] = pd.to_numeric(df[sutun], errors='coerce')

    df.fillna(0, inplace=True)

    print("\n--- TEMİZLENMİŞ VE SAYIYA ÇEVRİLMİŞ VERİ ---")
    print(df[['food', 'calories', 'fat']].head())
    
    print("\nTemizlik Başarılı! Makine öğrenmesine hazırız.")
   
    from sklearn.preprocessing import StandardScaler
    from sklearn.neighbors import NearestNeighbors

    ozellikler = ['calories', 'protein', 'fat', 'carbs']
    X = df[ozellikler]
    scaler = StandardScaler()
    X_olcekli = scaler.fit_transform(X)

    knn_model = NearestNeighbors(n_neighbors=4, metric='euclidean')
    
    knn_model.fit(X_olcekli)
    print("\nModel başarıyla eğitildi!")

    secilen_indeks = 4 
    mesafeler, komsu_indeksleri = knn_model.kneighbors([X_olcekli[secilen_indeks]])

    print("\n--- ÖNERİ SİSTEMİ ÇALIŞIYOR ---")
    print(f"Kullanıcının Seçtiği Besin: {df.iloc[secilen_indeks]['food']}")
    print("Buna Benzer Alternatif Öneriler:")
    
    for i in range(1, len(komsu_indeksleri[0])):
        komsu_idx = komsu_indeksleri[0][i]
        oneri_besin = df.iloc[komsu_idx]['food']
        oneri_kalori = df.iloc[komsu_idx]['calories']
        print(f"- {oneri_besin} (Kalori: {oneri_kalori})")
   
    secilen_besin_adi = df.iloc[secilen_indeks]['food']
    oneriler_listesi = [df.iloc[komsu_indeksleri[0][1]]['food'], 
                        df.iloc[komsu_indeksleri[0][2]]['food'], 
                        df.iloc[komsu_indeksleri[0][3]]['food']]

    conn_insert = psycopg2.connect(
        dbname="SaglikliOneriDB", user="postgres", password="12345", host="localhost", port="5432"
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
    print("\nBAŞARI: Makine öğrenmesi sonuçları veritabanına kalıcı olarak kaydedildi!")

except Exception as hata:
    print("Bir hata oluştu:", hata)