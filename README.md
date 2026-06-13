# Space Discovery Game 🚀

Bu proje, Python ve PyOpenGL kütüphaneleri kullanılarak geliştirilmiş, 3 aşamalı bir uzay keşif simülasyonu oyunudur. Oyuncu, Mars yüzeyindeki bir üsten başlayarak kalkış yapar, asteroit kuşaklarından geçerek Dünya'ya dikey iniş gerçekleştirmeye çalışır.

---

## 🌌 Proje Aşamaları

1. **Mars Keşif Modu (STATE_MARS_EXPLORE):** İlk şahıs (FP) kamera açısıyla Mars üssünün ve yüzeyinin keşfedildiği, nesne çarpışma testlerinin (AABB) aktif olduğu aşama.
2. **Uzay Uçuşu Modu (STATE_SPACE_FLIGHT):** Kokpit maskesi (HUD) arkasından siber yıldızlar, gezegenler ve karşıdan gelen meteorlar arasından geçerek Dünya'ya doğru ilerlenilen aşama.
3. **Dünya Dikey İniş Modu (STATE_EARTH_LANDING):** Geniş açılı üçüncü şahıs (TPP) kamera modunda, fizik tabanlı yerçekimi ivmesine karşı motor ateşleyerek güvenli iniş rampasına isabet etmeye çalışılan final aşaması.

---

## 🛠️ Kullanılan Kütüphaneler ve Teknolojiler

Projenin çalışması için bilgisayarınızda Python 3.13.3 sürümünün ve aşağıdaki bağımlılıkların yüklü olması gerekmektedir:

* **Pygame:** Pencere yönetimi, klavye/fare girdileri ve oyun döngüsü için.
* **PyOpenGL / PyOpenGL_accelerate:** 3B grafiklerin render edilmesi, matris manipülasyonları ve donanım hızlandırmalı çizimler için.
* **NumPy:** Matematiksel hesaplamalar ve dizi operasyonları için.

---

## 🚀 Kurulum ve Çalıştırma Adımları

### 1. Bağımlılıkların Yüklenmesi
Terminal veya komut satırını açarak aşağıdaki komut yardımıyla gerekli kütüphaneleri yükleyin:

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate numpy
```

### 2. Dosya Yapısı
Kodun hatasız çalışabilmesi için .obj modellerinin ve kaplamaların (textures) kök dizinde şu yapıda bulunması şarttır:
```bash
├── main.py
├── camera.py
├── obj_loader.py
├── collision.py
├── objects/
│   ├── spaceship.obj
│   ├── spaceship_chair.obj
│   ├── console1/
│   └── console2/
└── textures/
    ├── mars_ground.jpg
    └── spaceship_walls.jpg
```

### 3. Oyunu Başlatma
Proje dizinine gelip ana dosyayı çalıştırın:
```bash
python main.py
```

🎮 Kontrol Tuşları
1. Mars Keşif Modu Kontrolleri
W, A, S, D: Hareket Etme (İleri, Sol, Geri, Sağ)

Mouse (Fare): Bakış Açısını Değiştirme (360 Derece FP Kamera)

E: Uzay gemisine yaklaşınca uçuş modunu (kalkışı) başlatma.

2. Uzay Uçuşu Modu Kontrolleri
W: Gemiyi Hızlandırma (Hiper Sürücü)

A, D: Meteorlardan kaçmak için evreni sola/sağa kaydırma.

3. Dünya Dikey İniş Modu (TPP) Kontrolleri
Space (Boşluk Çubuğu): Roket motorlarını ateşler. Düşüş ivmesini kırar, dikey hızı yavaşlatır ve geminin altından katmanlı jet alevi fışkırtır.

A, D: Gemiyi yatay eksende sola ve sağa kaydırarak aşağıdaki sarı çizgili iniş rampasını ortalamayı sağlar.

Genel Kontroller
ESC: Oyundan çıkış yapar.

📊 Başarı Kriterleri (Final Aşaması)
Görevin başarıyla tamamlanabilmesi için uzay gemisi 12.0 irtifa sınırına ulaştığı anda:

İniş hızının 1.5 M/S değerinden az olması gerekir (Yumuşak İniş).

Geminin yatay X koordinatının ±6.0 sınırları içinde, yani tam sarı rampanın üzerinde olması gerekir (İsabetli İniş).