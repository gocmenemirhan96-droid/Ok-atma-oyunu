import pygame
import sys
import math
import random
import time
import json
import os

# 1. Pygame Baslat
pygame.init()

# Ekran boyutlarini dinamik al
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Tam ekran modunu ac
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Ok Atma Oyunu")
clock = pygame.time.Clock()

# --- RENKLER (GECE TEMASI) ---
GECE_SIYAHI = (20, 24, 35)       
BEYAZ = (245, 246, 250)
KIRMIZI = (255, 71, 87)
MAVI = (84, 160, 255)
SARI = (255, 165, 2)
YESIL = (46, 213, 115)
PARLAK_YESIL = (0, 230, 118)  
PEMBE = (255, 119, 182)
ACIK_MAVI = (52, 207, 241)
ACIK_YESIL = (144, 238, 144)
KUPA_TURUNCU = (230, 126, 34) 
ALEV_TURUNCU = (255, 69, 0)      
GRI = (170, 170, 170)
YILDIZ_SARI = (255, 253, 208)

# --- DINAMIK ARKA PLAN (YILDIZLAR) ---
# Dışarıdan görsel yüklemek yerine Android'de sorunsuz çalışan kodsal yıldızlar
yildizlar = []
for _ in range(40):
    yildizlar.append({
        "x": random.randint(0, SCREEN_WIDTH),
        "y": random.randint(0, SCREEN_HEIGHT),
        "boyut": random.randint(2, 4),
        "parlaklik": random.randint(150, 255),
        "hiz": random.choice([1, -1])
    })

# Oyun Ici Durum Yonetimi
durum = "YUKLEME"            
sonraki_durum = "ISIM_GIRIS"  

# Alt Menu Mod Secimi Kontrolu
mod_secimi_acik = False  

oyuncu_ismi = "" 
toplam_kupa = 0
gosterilen_kupa = 0  
skor = 0
can = 5

# Zamana Karsi Mod Degiskenleri
oyun_modu = "KLASIK"          
kalan_sure = 60
sure_zamanlayici = 0

# Kombo Sistemi Degiskenleri
kombo_sayaci = 0
atesli_ok_aktif = False

# Yukleme Ekrani Degiskenleri
yukleme_yuzdesi = 0
yukleme_hizi = 2.5 

# Ogretici Modu Degiskenleri
ogretici_sayac = 0  

# Her Karakterin Kendi Kupa Hafizasi
karakter_kupalari = {
    "BEYAZ": 0, 
    "PEMBE": 0,
    "KIRMIZI": 0,
    "MAVI": 0,
    "YESIL": 0,
    "ACIK MAVI": 0,
    "ACIK YESIL": 0
}

# --- SKOR HAFIZASI (JSON DOSYA YONETIMI) ---
# Android sistemlerinde güvenli dosya yolu (Çökme korumalı)
KAYIT_DOSYASI = "oyun_kayit.json"

def verileri_yukle():
    global oyuncu_ismi, toplam_kupa, gosterilen_kupa, karakter_kupalari, sonraki_durum
    if os.path.exists(KAYIT_DOSYASI):
        try:
            with open(KAYIT_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
                oyuncu_ismi = data.get("oyuncu_ismi", "")
                toplam_kupa = data.get("toplam_kupa", 0)
                gosterilen_kupa = toplam_kupa
                # Eski kayıttaki karakter kupalarını çek, yoksa varsayılanı koru
                kayitli_karakterler = data.get("karakter_kupalari", {})
                for k, v in kayitli_karakterler.items():
                    if k in karakter_kupalari:
                        karakter_kupalari[k] = v
                
                # Eğer oyuncu daha önce isim girdiyse doğrudan Ana Menüye geçsin
                if oyuncu_ismi.strip() != "":
                    sonraki_durum = "ANA_MENU"
        except Exception as e:
            print("Veri yukleme hatasi, varsayilan ayarlar aciliyor:", e)

def verileri_kaydet():
    try:
        data = {
            "oyuncu_ismi": oyuncu_ismi,
            "toplam_kupa": toplam_kupa,
            "karakter_kupalari": karakter_kupalari
        }
        with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Veri kaydetme hatasi:", e)

# Oyun açılır açılmaz eski skoru yükle
verileri_yukle()

# Cop Adam Renk Magazasi Ayarlari
secili_renk = (245, 246, 250) 
secili_renk_adi = "BEYAZ" 
acilan_bildirim = ""

# Animasyon Parcaciklari Listesi (Kupa Efekti)
kupa_parcaciklari = []

# Ok Ayarlari
ok_firlatildi = False
ok_x, ok_y = 0, 0
ok_hiz_x, ok_hiz_y = 0, 0
ok_aci = 0
ok_uzunluk = 110

# Hedef Ayarlari
hedef_x = SCREEN_WIDTH - int(SCREEN_WIDTH * 0.15)
hedef_y = SCREEN_HEIGHT // 2
hedef_yari_cap = 100
hedef_hiz = 12.0

# Kontroller
surukleniyor = False
dokunma_x, dokunma_y = 0, 0
guncel_aci = 0.0
gosterilecek_yazi = ""
yazi_zamanlayici = 0

ovgu_kelimeleri = ["HARIKA ATIS!", "HARIKA!", "GUZEL!", "COK GUZEL!", "ATISIN IYI!"]

# --- FONTLAR ---
font_kucuk = pygame.font.SysFont(None, 45)
font_uyari = pygame.font.SysFont(None, 40)
font_skor = pygame.font.SysFont(None, 60)
font_buton_orta = pygame.font.SysFont(None, 42)  
font_mod_buton = pygame.font.SysFont(None, 35)   
font_ovgu = pygame.font.SysFont(None, 90)
font_buyuk = pygame.font.SysFont(None, 110)

# Statik Kutular
rect_giri_kutusu = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 30, 500, 80)

def buton_olustur(x, y, g, yk):
    return pygame.Rect(x, y, g, yk)

def buton_ciz(metin, kutu, normal_renk, yazi_renk, ozel_font=None):
    pygame.draw.rect(screen, normal_renk, kutu, 0, 15)
    pygame.draw.rect(screen, BEYAZ, kutu, 2, 15) 
    kullanilacak_font = ozel_font if ozel_font else font_skor
    yazi_surf = kullanilacak_font.render(metin, True, yazi_renk)
    yazi_rect = yazi_surf.get_rect(center=kutu.center)
    screen.blit(yazi_surf, yazi_rect)

def kupa_ve_odul_guncelle(kazanilan_skor):
    global toplam_kupa, acilan_bildirim
    eski_kupa = toplam_kupa
    toplam_kupa += kazanilan_skor
    
    karakter_kupalari[secili_renk_adi] += kazanilan_skor
    
    # Skoru anında hafızaya kaydet kanka!
    verileri_kaydet()
    
    if eski_kupa < 100 <= toplam_kupa: acilan_bildirim = "100 Kupa Oldun!\nPembe Cop Adam Acildi!"
    elif eski_kupa < 200 <= toplam_kupa: acilan_bildirim = "200 Kupa Oldun!\nKirmizi Cop Adam Acildi!"
    elif eski_kupa < 500 <= toplam_kupa: acilan_bildirim = "500 Kupa Oldun!\nMavi Cop Adam Acildi!"
    elif eski_kupa < 800 <= toplam_kupa: acilan_bildirim = "800 Kupa Oldun!\nYesil Cop Adam Acildi!"
    elif eski_kupa < 900 <= toplam_kupa: acilan_bildirim = "900 Kupa Oldun!\nAcik Mavi Cop Adam Acildi!"
    elif eski_kupa < 1000 <= toplam_kupa: acilan_bildirim = "1000 Kupa Oldun!\nAcik Yesil Cop Adam Acildi!"

def renk_guncelle(mevcut_renk):
    global secili_renk, secili_renk_adi
    varsayilan_silah_renk = (245, 246, 250)
    if mevcut_renk == varsayilan_silah_renk and toplam_kupa >= 100:
        secili_renk = PEMBE; secili_renk_adi = "PEMBE"
    elif mevcut_renk == PEMBE and toplam_kupa >= 200:
        secili_renk = KIRMIZI; secili_renk_adi = "KIRMIZI"
    elif mevcut_renk == KIRMIZI and toplam_kupa >= 500:
        secili_renk = MAVI; secili_renk_adi = "MAVI"
    elif mevcut_renk == MAVI and toplam_kupa >= 800:
        secili_renk = YESIL; secili_renk_adi = "YESIL"
    elif mevcut_renk == YESIL and toplam_kupa >= 900:
        secili_renk = ACIK_MAVI; secili_renk_adi = "ACIK MAVI"
    elif mevcut_renk == ACIK_MAVI and toplam_kupa >= 1000:
        secili_renk = ACIK_YESIL; secili_renk_adi = "ACIK YESIL"
    else:
        secili_renk = varsayilan_silah_renk; secili_renk_adi = "BEYAZ"

def parcacik_olustur(baslangic_x, baslangic_y):
    for _ in range(8):
        parcacik = {
            "x": baslangic_x + random.randint(-15, 15),
            "y": baslangic_y + random.randint(-15, 15),
            "hedef_x": 220, 
            "hedef_y": 95,
            "hiz": random.uniform(12, 18)
        }
        kupa_parcaciklari.append(parcacik)

def yukleme_ekranini_baslat(hedef_durum):
    global durum, sonraki_durum, yukleme_yuzdesi
    yukleme_yuzdesi = 0
    sonraki_durum = hedef_durum
    durum = "YUKLEME"

def arka_plan_ciz():
    # Uzay hissi veren dinamik arka plan
    screen.fill(GECE_SIYAHI)
    for yildiz in yildizlar:
        # Yıldızların hafifçe göz kırpma animasyonu
        yildiz["parlaklik"] += yildiz["hiz"] * 3
        if yildiz["parlaklik"] >= 255 or yildiz["parlaklik"] <= 100:
            yildiz["hiz"] *= -1
        
        # Sınırlandırma
        yildiz["parlaklik"] = max(100, min(255, yildiz["parlaklik"]))
        
        renk = (yildiz["parlaklik"], yildiz["parlaklik"], int(yildiz["parlaklik"] * 0.8))
        pygame.draw.circle(screen, renk, (yildiz["x"], yildiz["y"]), yildiz["boyut"])

# Klavyeyi baslat
pygame.key.start_text_input()

while True:
    rect_kaydet_btn = buton_olustur(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 + 140, 440, 85)
    rect_oyna_ana_btn = buton_olustur(SCREEN_WIDTH - 280, SCREEN_HEIGHT - 130, 240, 90)
    
    mx = SCREEN_WIDTH // 2
    my = SCREEN_HEIGHT // 2 - 30
    
    rect_secim_hemen_oyna = buton_olustur(SCREEN_WIDTH // 2 - 320, SCREEN_HEIGHT // 2, 300, 90)
    rect_secim_ogretici = buton_olustur(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2, 300, 90)
    
    rect_mod_klasik = buton_olustur(mx - 320, my + 380, 300, 85)
    rect_mod_zaman = buton_olustur(mx - 320, my + 485, 300, 85)
    
    rect_tekrar_btn = buton_olustur(SCREEN_WIDTH // 2 - 290, SCREEN_HEIGHT // 2 + 100, 270, 85)
    rect_menu_btn = buton_olustur(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 + 100, 270, 85)
    
    rect_cop_kutu = buton_olustur(mx - 100, my - 60, 200, 350)

    cop_adam_kafa_x = int(SCREEN_WIDTH * 0.12)
    cop_adam_kafa_y = SCREEN_HEIGHT // 2 - 50
    cx = cop_adam_kafa_x + 60
    cy = cop_adam_kafa_y + 60
    
    if durum in ["OYUN", "OGRETICI"]:
        if surukleniyor:
            guncel_aci = math.atan2(cy - dokunma_y, cx - dokunma_x)
        elif not ok_firlatildi:
            guncel_aci = math.atan2(hedef_y - cy, hedef_x - cx)
    else:
        guncel_aci = 0.0

    cos_aci = math.cos(guncel_aci)
    sin_aci = math.sin(guncel_aci)
    yay_x = cx + cos_aci * 45
    yay_y = cy + sin_aci * 45

    if gosterilen_kupa < toplam_kupa:
        gosterilen_kupa += 1

    # --- 1. EVENT KONTROLLERi ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        elif event.type == pygame.TEXTINPUT and durum == "ISIM_GIRIS":
            if len(oyuncu_ismi) < 12:
                oyuncu_ismi += event.text

        elif event.type == pygame.KEYDOWN and durum == "ISIM_GIRIS":
            if event.key == pygame.K_BACKSPACE:
                oyuncu_ismi = oyuncu_ismi[:-1]
            elif event.key == pygame.K_RETURN:
                if oyuncu_ismi.strip() == "":
                    oyuncu_ismi = "Oyuncu 1"
                verileri_kaydet() # Ismi ilk kez kaydet
                pygame.key.stop_text_input()
                durum = "SECIM_EKRANI"

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            if durum == "ISIM_GIRIS":
                if rect_kaydet_btn.collidepoint(pos):
                    if oyuncu_ismi.strip() == "":
                        oyuncu_ismi = "Oyuncu 1"
                    verileri_kaydet() # Ismi kaydet
                    pygame.key.stop_text_input()
                    durum = "SECIM_EKRANI"
                elif rect_giri_kutusu.collidepoint(pos):
                    pygame.key.start_text_input()

            elif durum == "SECIM_EKRANI":
                if rect_secim_hemen_oyna.collidepoint(pos):
                    yukleme_ekranini_baslat("ANA_MENU")
                elif rect_secim_ogretici.collidepoint(pos):
                    ogretici_sayac = 0
                    ok_firlatildi = False
                    surukleniyor = False
                    hedef_y = SCREEN_HEIGHT // 2  
                    yukleme_ekranini_baslat("OGRETICI")

            elif durum == "ANA_MENU":
                if acilan_bildirim != "":
                    acilan_bildirim = ""
                else:
                    if rect_oyna_ana_btn.collidepoint(pos):
                        mod_secimi_acik = not mod_secimi_acik 
                        
                    elif mod_secimi_acik and rect_mod_klasik.collidepoint(pos):
                        oyun_modu = "KLASIK"
                        skor = 0
                        can = 5
                        kombo_sayaci = 0
                        atesli_ok_aktif = False
                        ok_firlatildi = False
                        surukleniyor = False
                        hedef_hiz = 12.0
                        mod_secimi_acik = False
                        yukleme_ekranini_baslat("OYUN")
                        
                    elif mod_secimi_acik and rect_mod_zaman.collidepoint(pos):
                        oyun_modu = "ZAMAN_KARSI"
                        skor = 0
                        kalan_sure = 60
                        sure_zamanlayici = pygame.time.get_ticks()
                        kombo_sayaci = 0
                        atesli_ok_aktif = False
                        ok_firlatildi = False
                        surukleniyor = False
                        hedef_hiz = 17.0  
                        mod_secimi_acik = False
                        yukleme_ekranini_baslat("OYUN")
                        
                    elif rect_cop_kutu.collidepoint(pos):
                        renk_guncelle(secili_renk)
                        mod_secimi_acik = False 

            elif durum in ["OYUN", "OGRETICI"] and not ok_firlatildi:
                surukleniyor = True
                dokunma_x, dokunma_y = pos[0], pos[1]
                
            elif durum in ["OYUN_BITTI", "OGRETICI_BITTI"]:
                if rect_tekrar_btn.collidepoint(pos):
                    if durum == "OGRETICI_BITTI":
                        oyun_modu = "KLASIK"
                        skor = 0
                        can = 5
                        kombo_sayaci = 0
                        atesli_ok_aktif = False
                        ok_firlatildi = False
                        surukleniyor = False
                        hedef_hiz = 12.0
                        yukleme_ekranini_baslat("OYUN")
                    else:
                        kupa_ve_odul_guncelle(skor)
                        skor = 0
                        can = 5
                        kalan_sure = 60
                        kombo_sayaci = 0
                        atesli_ok_aktif = False
                        ok_firlatildi = False
                        surukleniyor = False
                        hedef_hiz = 12.0 if oyun_modu == "KLASIK" else 17.0
                        yukleme_ekranini_baslat("OYUN")
                        
                elif rect_menu_btn.collidepoint(pos):
                    if durum != "OGRETICI_BITTI":
                        kupa_ve_odul_guncelle(skor)
                    durum = "ANA_MENU"

        elif event.type == pygame.MOUSEMOTION and durum in ["OYUN", "OGRETICI"] and surukleniyor:
            event_x, event_y = event.pos[0], event.pos[1]
            if durum == "OGRETICI" and ok_firlatildi:
                pass
            else:
                dokunma_x, dokunma_y = event_x, event_y
            
        elif event.type == pygame.MOUSEBUTTONUP and durum in ["OYUN", "OGRETICI"] and surukleniyor:
            surukleniyor = False
            dx = yay_x - dokunma_x
            dy = yay_y - dokunma_y
            uzaklik = math.sqrt(dx**2 + dy**2)
            if uzaklik > 15:
                ok_aci = math.atan2(dy, dx)
                guc = min(uzaklik * 0.13, 30)
                ok_hiz_x = math.cos(ok_aci) * guc
                ok_hiz_y = math.sin(ok_aci) * guc
                ok_x, ok_y = yay_x, yay_y
                ok_firlatildi = True

    # --- 2. OYUN HAREKET MANTIGI ---
    if durum == "YUKLEME":
        yukleme_yuzdesi += yukleme_hizi
        if yukleme_yuzdesi >= 100:
            yukleme_yuzdesi = 100
            screen.fill((0, 0, 0))
            y_metin = font_skor.render("OYUN YUKLENIYOR LUTFEN BEKLEYINIZ...", True, BEYAZ)
            screen.blit(y_metin, y_metin.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)))
            pygame.display.flip()
            time.sleep(0.8)
            
            if sonraki_durum == "OYUN" and oyun_modu == "ZAMAN_KARSI" or (sonraki_durum == "OYUN" and durum == "OGRETICI_BITTI"):
                sure_zamanlayici = pygame.time.get_ticks()
            durum = sonraki_durum

    elif durum == "OYUN":
        if oyun_modu == "ZAMAN_KARSI":
            su_an = pygame.time.get_ticks()
            gecen_sure = (su_an - sure_zamanlayici) // 1000
            kalan_sure = 60 - gecen_sure
            if kalan_sure <= 0:
                kalan_sure = 0
                durum = "OYUN_BITTI"

        hedef_y += hedef_hiz
        if hedef_y - hedef_yari_cap < 40 or hedef_y + hedef_yari_cap > SCREEN_HEIGHT - 40:
            hedef_hiz *= -1

        if ok_firlatildi:
            ok_x += ok_hiz_x
            ok_y += ok_hiz_y
            ok_hiz_y += 0.20
            ok_aci = math.atan2(ok_hiz_y, ok_hiz_x)
            
            ok_uc_x = ok_x + math.cos(ok_aci) * ok_uzunluk
            ok_uc_y = ok_y + math.sin(ok_aci) * ok_uzunluk
            
            fark_x = ok_uc_x - hedef_x
            fark_y = ok_uc_y - hedef_y
            mesafe = math.sqrt(fark_x**2 + fark_y**2)
            
            if mesafe <= hedef_yari_cap:
                kombo_sayaci += 1
                eklenecek_kupa = 10 if atesli_ok_aktif else 5
                skor += eklenecek_kupa
                if kombo_sayaci >= 3: atesli_ok_aktif = True
                
                parcacik_olustur(ok_uc_x, ok_uc_y)
                
                ok_firlatildi = False
                hedef_y = random.randint(150, SCREEN_HEIGHT - 150)
                gosterilecek_yazi = f"ATESLI ATIS! KOMBO x{kombo_sayaci}" if atesli_ok_aktif else random.choice(ovgu_kelimeleri) + f" (x{kombo_sayaci})"
                yazi_zamanlayici = 60
            
            if ok_x > SCREEN_WIDTH + 100 or ok_y > SCREEN_HEIGHT + 100 or ok_y < -100:
                ok_firlatildi = False
                kombo_sayaci = 0       
                atesli_ok_aktif = False 
                if oyun_modu == "KLASIK":
                    can -= 1
                    if can <= 0: durum = "OYUN_BITTI"

        for p in kupa_parcaciklari[:]:
            p_dx = p["hedef_x"] - p["x"]
            p_dy = p["hedef_y"] - p["y"]
            p_dist = math.sqrt(p_dx**2 + p_dy**2)
            if p_dist < 20: 
                kupa_parcaciklari.remove(p)
            else:
                p["x"] += (p_dx / p_dist) * p["hiz"]
                p["y"] += (p_dy / p_dist) * p["hiz"]

    elif durum == "OGRETICI":
        if ok_firlatildi:
            ok_x += ok_hiz_x
            ok_y += ok_hiz_y
            ok_hiz_y += 0.20
            ok_aci = math.atan2(ok_hiz_y, ok_hiz_x)
            
            ok_uc_x = ok_x + math.cos(ok_aci) * ok_uzunluk
            ok_uc_y = ok_y + math.sin(ok_aci) * ok_uzunluk
            
            fark_x = ok_uc_x - hedef_x
            fark_y = ok_uc_y - hedef_y
            mesafe = math.sqrt(fark_x**2 + fark_y**2)
            
            if mesafe <= hedef_yari_cap:
                ogretici_sayac += 1
                parcacik_olustur(ok_uc_x, ok_uc_y)
                ok_firlatildi = False
                if ogretici_sayac >= 4:
                    durum = "OGRETICI_BITTI"
            
            if ok_x > SCREEN_WIDTH + 100 or ok_y > SCREEN_HEIGHT + 100 or ok_y < -100:
                ok_firlatildi = False  

        for p in kupa_parcaciklari[:]:
            p_dx = p["hedef_x"] - p["x"]
            p_dy = p["hedef_y"] - p["y"]
            p_dist = math.sqrt(p_dx**2 + p_dy**2)
            if p_dist < 20: kupa_parcaciklari.remove(p)
            else:
                p["x"] += (p_dx / p_dist) * p["hiz"]
                p["y"] += (p_dy / p_dist) * p["hiz"]

    # --- 3. CIZIMLER ---
    if durum == "YUKLEME":
        screen.fill((0, 0, 0))
        y_metin = font_skor.render("OYUN YUKLENIYOR LUTFEN BEKLEYINIZ...", True, BEYAZ)
        screen.blit(y_metin, y_metin.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)))
        
        yuzde_metin = font_skor.render(f"%{int(yukleme_yuzdesi)}", True, KUPA_TURUNCU)
        screen.blit(yuzde_metin, yuzde_metin.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10)))
        
        bar_max_genislik = 500
        bar_guncel_genislik = int((yukleme_yuzdesi / 100) * bar_max_genislik)
        arka_bar = pygame.Rect(SCREEN_WIDTH // 2 - bar_max_genislik // 2, SCREEN_HEIGHT // 2 + 30, bar_max_genislik, 35)
        pygame.draw.rect(screen, (30, 30, 30), arka_bar, 0, 8)
        if bar_guncel_genislik > 0:
            dolan_bar = pygame.Rect(SCREEN_WIDTH // 2 - bar_max_genislik // 2, SCREEN_HEIGHT // 2 + 30, bar_guncel_genislik, 35)
            pygame.draw.rect(screen, KUPA_TURUNCU, dolan_bar, 0, 8)
        pygame.draw.rect(screen, GRI, arka_bar, 3, 8)

    else:
        # Harika yıldızlı arka planı çizdir
        arka_plan_ciz()

        if durum == "ISIM_GIRIS":
            baslik_surf = font_buyuk.render("OK ATMA OYUNU", True, BEYAZ)
            screen.blit(baslik_surf, baslik_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 190)))
            yazi_soru = font_skor.render("Lutfen Ismini Yaz kanka:", True, GRI)
            screen.blit(yazi_soru, yazi_soru.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)))
            pygame.draw.rect(screen, BEYAZ, rect_giri_kutusu, 2, 10)
            
            display_isim = oyuncu_ismi if oyuncu_ismi != "" else "Yaz veya bos birak..."
            isim_surf = font_skor.render(display_isim, True, KUPA_TURUNCU if oyuncu_ismi != "" else GRI)
            screen.blit(isim_surf, isim_surf.get_rect(center=rect_giri_kutusu.center))
            
            uyari_text = "Bilgilendirme: Bu isim kalicidir, degistirilemez!"
            uyari_surf = font_uyari.render(uyari_text, True, KIRMIZI)
            screen.blit(uyari_surf, uyari_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)))
            buton_ciz("DEVAM ET", rect_kaydet_btn, PARLAK_YESIL, GECE_SIYAHI)

        elif durum == "SECIM_EKRANI":
            soru_surf = font_skor.render("Nasıl Başlamak İstersin Kanka?", True, BEYAZ)
            screen.blit(soru_surf, soru_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120)))
            
            buton_ciz("HEMEN OYNA", rect_secim_hemen_oyna, PARLAK_YESIL, GECE_SIYAHI, font_buton_orta)
            buton_ciz("OGRETICI", rect_secim_ogretici, MAVI, GECE_SIYAHI, font_buton_orta)

        elif durum == "ANA_MENU":
            kupa_kutusu = pygame.Rect(40, 40, 360, 115)
            pygame.draw.rect(screen, KUPA_TURUNCU, kupa_kutusu, 0, 15)
            pygame.draw.rect(screen, BEYAZ, kupa_kutusu, 2, 15)
            screen.blit(font_skor.render(f"KUPA: {gosterilen_kupa}", True, BEYAZ), (60, 50))
            screen.blit(font_kucuk.render(f"Oyuncu: {oyuncu_ismi}", True, BEYAZ), (60, 105))

            karakter_kupa_skor = karakter_kupalari[secili_renk_adi]
            skor_kutu_surf = font_kucuk.render(f"SKOR: {karakter_kupa_skor}", True, KUPA_TURUNCU)
            screen.blit(skor_kutu_surf, skor_kutu_surf.get_rect(center=(mx, my - 95)))

            # Cop Adam Cizimi
            pygame.draw.circle(screen, secili_renk, (mx, my), 55, 7)
            pygame.draw.line(screen, secili_renk, (mx, my + 55), (mx, my + 195), 7)
            pygame.draw.line(screen, secili_renk, (mx, my + 90), (mx - 65, my + 155), 7)
            pygame.draw.line(screen, secili_renk, (mx, my + 90), (mx + 65, my + 155), 7)
            pygame.draw.line(screen, secili_renk, (mx, my + 195), (mx - 55, my + 285), 7)
            pygame.draw.line(screen, secili_renk, (mx, my + 195), (mx + 55, my + 285), 7)
            
            bilgi_surf = font_kucuk.render(f"Secili: {secili_renk_adi} (Degistirmek icin tikla)", True, BEYAZ)
            screen.blit(bilgi_surf, bilgi_surf.get_rect(center=(mx, my + 330)))

            buton_ciz("OYNA", rect_oyna_ana_btn, PARLAK_YESIL, GECE_SIYAHI)

            if mod_secimi_acik:
                buton_ciz("KLASIK MOD", rect_mod_klasik, YESIL, GECE_SIYAHI, font_mod_buton)
                tanim_klasik = font_mod_buton.render("- 5 Canla En Yuksek Skora Ulas!", True, GRI)
                screen.blit(tanim_klasik, (rect_mod_klasik.right + 25, rect_mod_klasik.centery - 12))
                
                buton_ciz("ZAMANA KARSI", rect_mod_zaman, MAVI, GECE_SIYAHI, font_mod_buton)
                tanim_zaman = font_mod_buton.render("- 60 Saniyede Hedefleri Avla!", True, GRI)
                screen.blit(tanim_zaman, (rect_mod_zaman.right + 25, rect_mod_zaman.centery - 12))

        elif durum in ["OYUN", "OGRETICI"]:
            kupa_oyun_kutu = pygame.Rect(40, 40, 440, 115)
            pygame.draw.rect(screen, KUPA_TURUNCU, kupa_oyun_kutu, 0, 15)
            pygame.draw.rect(screen, BEYAZ, kupa_oyun_kutu, 2, 15)
            
            if durum == "OGRETICI":
                screen.blit(font_skor.render("OGRETICI MODU", True, BEYAZ), (60, 50))
                screen.blit(font_kucuk.render(f"BASARILI ATIS: {ogretici_sayac} / 4", True, SARI), (60, 105))
                
                if surukleniyor and not ok_firlatildi:
                    talimat_surf = font_ovgu.render("SIMDI OKU ATMA ZAMANI!", True, PARLAK_YESIL)
                    screen.blit(talimat_surf, talimat_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 5)))
            else:
                screen.blit(font_skor.render(f"KUPA: {gosterilen_kupa}", True, BEYAZ), (60, 50))
                if oyun_modu == "KLASIK":
                    screen.blit(font_kucuk.render(f"CAN: {can} | MAC SKORU: {skor}", True, BEYAZ), (60, 105))
                else:
                    screen.blit(font_kucuk.render(f"SURE: {kalan_sure}s | MAC SKORU: {skor}", True, BEYAZ), (60, 105))

            if durum == "OYUN" and kombo_sayaci > 0:
                k_renk = ALEV_TURUNCU if atesli_ok_aktif else SARI
                k_metin = "ATESLI OK AKTIF!" if atesli_ok_aktif else f"KOMBO: x{kombo_sayaci}"
                screen.blit(font_skor.render(k_metin, True, k_renk), (40, 170))

            if durum == "OYUN" and yazi_zamanlayici > 0:
                y_renk = ALEV_TURUNCU if "ATESLI" in gosterilecek_yazi else PARLAK_YESIL
                ovgu_yuzeyi = font_ovgu.render(gosterilecek_yazi, True, y_renk)
                screen.blit(ovgu_yuzeyi, ovgu_yuzeyi.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 5)))
                yazi_zamanlayici -= 1

            # Hedef Tahtasi
            pygame.draw.circle(screen, KIRMIZI, (hedef_x, int(hedef_y)), int(hedef_yari_cap))
            pygame.draw.circle(screen, MAVI, (hedef_x, int(hedef_y)), int(hedef_yari_cap * 0.7))
            pygame.draw.circle(screen, SARI, (hedef_x, int(hedef_y)), int(hedef_yari_cap * 0.4))

            # Cop Adam
            kx, ky = cop_adam_kafa_x, cop_adam_kafa_y
            pygame.draw.line(screen, secili_renk, (kx, ky + 40), (kx, ky + 180), 6)
            pygame.draw.line(screen, secili_renk, (kx, ky + 180), (kx - 50, ky + 260), 6)
            pygame.draw.line(screen, secili_renk, (kx, ky + 180), (kx + 50, ky + 260), 6)
            pygame.draw.line(screen, secili_renk, (kx, ky + 70), (kx - 50, ky + 130), 6)
            pygame.draw.circle(screen, secili_renk, (kx, ky), 40, 6)
            kol_uc_x = int(kx + cos_aci * 70)
            kol_uc_y = int(ky + 70 + sin_aci * 15)
            pygame.draw.line(screen, secili_renk, (kx, ky + 70), (kol_uc_x, kol_uc_y), 6)

            # Yay
            ux = int(yay_x + math.cos(guncel_aci - 1.57) * 90)
            uy = int(yay_y + math.sin(guncel_aci - 1.57) * 90)
            ax = int(yay_x + math.cos(guncel_aci + 1.57) * 90)
            ay = int(yay_y + math.sin(guncel_aci + 1.57) * 90)
            pygame.draw.line(screen, BEYAZ, (ux, uy), (ax, ay), 2)
            
            noktalar = []
            for degisken_aci in range(-90, 91, 15):
                rad = guncel_aci + math.radians(degisken_aci)
                nx = int(yay_x + math.cos(rad) * 90 - cos_aci * 25)
                ny = int(yay_y + math.sin(rad) * 90 - sin_aci * 25)
                noktalar.append((nx, ny))
            pygame.draw.lines(screen, BEYAZ, False, noktalar, 7)

            # --- YEŞİL NİŞAN NOKTALARI ---
            if surukleniyor and not ok_firlatildi:
                sim_dx = yay_x - dokunma_x
                sim_dy = yay_y - dokunma_y
                sim_uzaklik = math.sqrt(sim_dx**2 + sim_dy**2)
                if sim_uzaklik > 15:
                    sim_aci = math.atan2(sim_dy, sim_dx)
                    sim_guc = min(sim_uzaklik * 0.13, 30)
                    sim_hiz_x = math.cos(sim_aci) * sim_guc
                    sim_hiz_y = math.sin(sim_aci) * sim_guc
                    
                    sim_x, sim_y = yay_x, yay_y
                    sim_gravitasyon = 0.20
                    
                    for step in range(1, 55):
                        sim_x += sim_hiz_x
                        sim_y += sim_hiz_y
                        sim_hiz_y += sim_gravitasyon
                        if step % 3 == 0:
                            pygame.draw.circle(screen, PARLAK_YESIL, (int(sim_x), int(sim_y)), 7)

            # Ok Cizimi
            ok_rengi = ALEV_TURUNCU if atesli_ok_aktif else BEYAZ
            if ok_firlatildi:
                bx = int(ok_x + math.cos(ok_aci) * ok_uzunluk)
                by = int(ok_y + math.sin(ok_aci) * ok_uzunluk)
                pygame.draw.line(screen, ok_rengi, (int(ok_x), int(ok_y)), (bx, by), 8)
                pygame.draw.circle(screen, KIRMIZI if not atesli_ok_aktif else SARI, (bx, by), 8)
            else:
                bx = int(yay_x + cos_aci * ok_uzunluk)
                by = int(yay_y + sin_aci * ok_uzunluk)
                pygame.draw.line(screen, ok_rengi, (int(yay_x), int(yay_y)), (bx, by), 8)

            # Altın Sarısı Kupa Efektleri
            for p in kupa_parcaciklari:
                pygame.draw.circle(screen, KUPA_TURUNCU, (int(p["x"]), int(p["y"])), 15)
                pygame.draw.circle(screen, BEYAZ, (int(p["x"]), int(p["y"])), 15, 2)

        elif durum in ["OYUN_BITTI", "OGRETICI_BITTI"]:
            if durum == "OGRETICI_BITTI":
                bitti_surf = font_buyuk.render("OGRETICIYI BITIRDIN BRAVO!", True, PARLAK_YESIL)
                screen.blit(bitti_surf, bitti_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120)))
                
                alt_surf = font_skor.render("Mekanikleri Kavradın, Macera Başlıyor!", True, BEYAZ)
                screen.blit(alt_surf, alt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))
            else:
                bitis_sebebi = "SUREN BITTI!" if oyun_modu == "ZAMAN_KARSI" else "HAKLARIN BITTI!"
                bitti_surf = font_buyuk.render(bitis_sebebi, True, KIRMIZI)
                screen.blit(bitti_surf, bitti_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120)))
                
                skor_surf = font_skor.render(f"Bu Elde Kazandigin Kupa: +{skor}", True, BEYAZ)
                screen.blit(skor_surf, skor_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))

            # Butonlar
            buton_ciz("TEKRAR OYNA", rect_tekrar_btn, PARLAK_YESIL, GECE_SIYAHI, font_buton_orta)
            buton_ciz("ANA MENU", rect_menu_btn, MAVI, GECE_SIYAHI, font_buton_orta)

    pygame.display.flip()
    clock.tick(60)

