# 🔬 Faz 1: Ağ Temelleri, Alt Ağlar & İzolasyon (Subnets & Isolation)

Bu laboratuvar; bilgisayar ağlarını hiç bilmeyen birinin bile zihninde net bir resim oluşturabilmesi için tasarlanmıştır. Bu rehberde **MAC adresi**, **IP adresi**, **Subnet Mask (/24)**, **VLAN/Köprü İzolasyonu** ve **ARP (Adres Çözümleme Protokolü)** kavramlarını günlük hayat analojileri ve Docker üzerinde canlı komutlarla inceleyeceğiz.

---

## 🧠 Sıfırdan Başlayanlar İçin: Temel Kavramlar Sözlüğü

Laboratuvara başlamadan önce, ekranda göreceğimiz kavramları en yalın haliyle anlayalım:

### 1. VLAN Nedir? "Tek Fiziksel Altyapıyı Bölmek" Ne Anlama Gelir?

#### 🔌 A. Gerçek Dünyadaki Fiziksel Katman (Dokunabildiğimiz Şeyler):
Bir şirketin sistem odasına (sunucu odasına) girdiğinizde gözünüzle gördüğünüz donanımlar şunlardır:
1. **Bilgisayarlar:** Masalardaki Ahmet'in ve Mehmet'in kasaları, arkadaki muhasebe sunucusu.
2. **Kablolar:** Masaların altından duvarların içinden geçen, ucu tırnaklı (RJ45 konnektörlü) bakır **Ethernet kabloları** (Cat6).
3. **Switch (Ağ Anahtarı / Dağıtıcı Kutu):** Duvardan gelen 24 veya 48 adet kablonun ucuca takıldığı, üzerinde sarı-yeşil ışıkları yanıp sönen **metal, dikdörtgen donanım kutusu**.

İşte **"Fiziksel Altyapı"** tam olarak bu **tek bir metal Switch kutusu, tek bir anakart ve içine giren bakır kablolardır.**

```text
               ┌─────────────────────────────────────────────────────────┐
               │    TEK BİR FİZİKSEL SWITCH KUTUSU (Metal Donanım)      │
               │                                                         │
Port Numaraları│ [1] [2] [3] [4] ... [11] [12] [13] ... [24]              │
               └─┬───┬────────────────┬──────────────────────────────────┘
                 │   │                │
      Mavi Kablo │   │ Mavi Kablo     │ Kırmızı Kablo
                 ▼   ▼                ▼
             Ahmet  Mehmet        Muhasebe Sunucusu
```

---

#### 📜 B. VLAN İcat Edilmeden Önce Ne Yapılıyordu? (Eski Usul / Fiziksel İzolasyon):
1990'ların başında VLAN (Virtual LAN) teknolojisi henüz yokken, şirketler Ahmet'in bilgisayarını Muhasebe sunucusundan ayırmak için **mecburen şunu yapıyordu:**
* Gidip piyasadan **iki ayrı fiziksel Switch kutusu** satın alıyorlardı.
* **1. Kutuya** sadece personelin mavi kabloları takılıyordu.
* **2. Kutuya** sadece muhasebenin kırmızı kabloları takılıyordu.
* İki kutu arasına hiçbir kablo çekilmiyordu.
* **Büyük İsraf:** Muhasebede sadece 2 sunucu varken koca 24 portlu kutunun 22 deliği boş kalıyor; binlerce dolar masraf ve kablo karmaşası oluyordu.

---

#### ✂️ C. VLAN Nasıl Devreye Girdi? (Yazılımla Çelik Duvar Örmek):
Mühendisler dedi ki: *"Neden her oda için yeni bir metal kutu alalım? Tek bir switch alalım, switch'in beynindeki işletim sistemine girip portların arasına **yazılımsal çelik duvarlar** örelim!"*

Ağ uzmanı switch'in komut satırına girer:
* *"Port 1 ile 10 arasındaki delikler: Siz artık **VLAN 10 (Personel Odası)** oldunuz!"*
* *"Port 11 ile 20 arasındaki delikler: Siz artık **VLAN 20 (Muhasebe Odası)** oldunuz!"*

**Metal Kutunun İçinde Ne Değişir? (ASIC Çipi):**  
Switch'in anakartındaki işlemci çipi (ASIC) artık bir güvenlik görevlisi gibi çalışır. Ahmet Port 1'den bir veri fırlattığında çip der ki:  
*"Bu elektrik sinyali Port 1'den geldi. Port 1 ise VLAN 10 odasına ait. Ben bu paketi Port 11'e (Muhasebeye) ASLA GEÇİRMEM!"*  
Yani aynı metal kutunun içinde olmalarına rağmen elektrik sinyalleri mantıksal olarak birbirinden tamamen yalıtılır.

---

#### 🐳 D. Docker'daki Birebir Karşılığı:
Bilgisayarınızda fiziksel bir Cisco switch kutusu yoktur; ancak Docker Linux çekirdeğinin (Kernel) içinde **sanal ağ donanımları** yaratır:

| Gerçek Fiziksel Ağ Dünyası | Bizim Docker Laboratuvarındaki Karşılığı |
| :--- | :--- |
| **Fiziksel Switch Kutusu** | **Docker Bridge (Sanal Köprü):** Linux'un RAM belleğinde çalışan yazılımsal sanal switch. |
| **Fiziksel Ethernet Kablosu (Cat6)** | **`veth` (Virtual Ethernet):** Docker'ın container ile köprü arasına çektiği sanal kablo. |
| **VLAN 10 (Personel Odası)** | `docker-compose.yml` içindeki **`vlan10_personel`** ağı (Subnet: `10.10.1.0/24`). |
| **VLAN 20 (Muhasebe Odası)** | `docker-compose.yml` içindeki **`vlan20_sunucu`** ağı (Subnet: `10.20.1.0/24`). |
| **Ahmet'in Fiziksel Bilgisayarı** | **`ahmet-pc` Container'ı** (Kendi sanal `eth0` kartı olan yalıtılmış kutu). |

Siz `docker compose up -d` dediğinizde Docker; tek bir bilgisayarın işlemci ve RAM'i üzerinde iki bağımsız sanal switch (`vlan10` ve `vlan20`) oluşturur ve aralarına hiçbir geçiş kablosu koymaz!

---

#### 🌉 E. Neden `docker-compose.yml` Dosyasında `driver: bridge` Seçtik? (Bridge Modunun Sırrı):

Ağ mühendisliği terminolojisinde **"Bridge (Köprü)"**, Katman 2'de (Data Link Katmanı) çalışan ve paketleri **fiziksel MAC adreslerine bakarak anahtarlayan (Switching yapan)** cihaz demektir. Yani modern dünyada:
$$\mathbf{Bridge \approx Sanal\ Switch}$$

Docker'da container çalıştırırken seçebileceğiniz farklı ağ sürücüleri (driver) vardır; fakat bu senaryoda **`driver: bridge`** seçmemizin çok hayati 3 sebebi vardır:

1. **İki Ayrı Yazılımsal Switch (Tam İzolasyon) Yaratmak:**  
   Docker'a `driver: bridge` dediğimizde, Linux çekirdeğinde birbirinden bağımsız iki adet sanal switch arayüzü (`br-xxxx` ve `br-yyyy`) yaratılır. Bu sayede `vlan10` switch'ine bağlı olan Ahmet ile `vlan20` switch'ine bağlı olan Muhasebe arasında donanım/yazılım seviyesinde çelik bir duvar örülmüş olur.

2. **Özel Alt Ağ (Subnetting) ve Sabit IP Belirleyebilmek:**  
   `bridge` sürücüsü sayesinde ağın IP havuzunu (`subnet: 10.10.1.0/24`), kapı numarasını (`gateway: 10.10.1.1`) ve container'ların sabit IP adreslerini (`ipv4_address: 10.10.1.45`) santim santim kendimiz yönetebiliriz.

3. **Diğer Modları Neden Seçmedik? (Karşılaştırma):**
   * **Neden `host` Modu Değil?**  
     `host` modunu seçseydik, container'ların hiçbir bağımsız sanal ağ kartı veya IP'si olmazdı; doğrudan sizin Windows/Linux ana makinenizin gerçek IP'sini paylaşırlardı. Dolayısıyla ortada ne iki ayrı alt ağ ne de bir ağ izolasyonu kalırdı!
   * **Neden `none` Modu Değil?**  
     `none` modunda container'ın içine hiçbir ağ kartı takılmaz (sadece `127.0.0.1` kalır). Cihaz dünyadan tamamen kopar; aynı odadaki arkadaşına bile ping atamaz.
   * **Neden `macvlan` Değil?**  
     `macvlan`, container'ı evdeki gerçek fiziksel Wi-Fi/Ethernet modeminize bağlar. Bu mod ev ağında bağımsız IP almak için harikadır; fakat bizim amacımız kendi içimizde izole laboratuvar alt ağları kurmaktır.

Özetle: **`driver: bridge`**, bilgisayarınızın içinde sıfır maliyetle onlarca **sanal Cisco switch** oluşturup aralarında gerçekçi ağ simülasyonları yapmanın tek ve en doğru yoludur!

---

### 2. IP Adresi ve Subnet Mask (`/24`) Nedir? (Mahalle ve Daire Benzetmesi)

Bir IP adresine (`10.10.1.45`) baktığınızda bilgisayar bu sayıyı ikiye böler:
1. **Mahalle / Site Adı (Network ID):** O sokaktaki herkes için ortaktır.
2. **Daire Numarası (Host ID):** Sadece o bilgisayara aittir.

> ❓ **Soru:** Bilgisayar `10.10.1.45` sayısının neresinin Mahalle, neresinin Daire olduğunu nereden anlar?  
> 👉 **Cevap:** Bunu bilgisayara fısıldayan şablona **Subnet Mask (Alt Ağ Maskesi)** denir!

| Cihaz | IP Adresi | Maske | Mahalle Adı (İlk 3 Kısım) | Daire No (Son Kısım) |
| :--- | :--- | :---: | :--- | :---: |
| **Ahmet'in PC'si** | `10.10.1 . 45` | `/24` | **`10.10.1` Mahallesi** | No: **45** |
| **Mehmet'in PC'si**| `10.10.1 . 46` | `/24` | **`10.10.1` Mahallesi** | No: **46** |
| **Muhasebe Sunucusu**| `10.20.1 . 50` | `/24` | **`10.20.1` Mahallesi** | No: **50** |

* **`/24` Ne Demektir?**  
  Bir IPv4 adresi 32 bittir. `/24` demek: *"İlk 24 biti (yani ilk 3 sayıyı) Mahalle Adı olarak kilitle, son 8 biti (son sayıyı) daire numaraları için serbest bırak!"* demektir.
* Ahmet ve Mehmet'in ilk 3 sayısı aynıdır (**`10.10.1`**). Yani ikisi **aynı odanın/mahallenin içindedir** ve doğrudan konuşabilirler.
* Muhasebe sunucusunun ilk 3 sayısı ise **`10.20.1`**'dir (10 yerine 20). Yani **tamamen farklı bir ilçededir!**

---

### 3. MAC Adresi ile IP Adresi Arasındaki Fark Nedir?
* **MAC Adresi (`d2:ef:39:...`):** Cihazın **T.C. Kimlik Numarasıdır**. Üretici tarafından ağ kartına kazınmıştır, cihaz nereye taşınırsa taşınsın sabittir.
* **IP Adresi (`10.10.1.45`):** Cihazın **Evinin Posta Adresidir**. Ahmet laptopu alıp kafeye giderse IP'si değişir, ofise gelirse tekrar değişir.
* **Kritik Kural:** Kablolar ve switch'ler paketleri son noktada teslim ederken IP'ye değil; cihazın donanım kimliği olan **MAC adresine** bakar!

---

## 🏗️ Laboratuvar Mimarisi

```text
       [ vlan10_personel Sanal Odası (10.10.1.0/24) ]
             │                                    │
             ▼                                    ▼
     [ ahmet-pc ]                          [ mehmet-pc ]
    (10.10.1.45)                          (10.10.1.46)
    (MAC: d2:ef:...)                      (MAC: 76:ae:...)
          │
          │ ❌ ÇELİK DUVAR (Farklı Alt Ağ - Arada Router Yok / İzolasyon)
          ▼
 [ vlan20_sunucu Sanal Odası (10.20.1.0/24) ]
             │
             ▼
    [ gizli-muhasebe ]
      (10.20.1.50)
```

---

## 🚀 Laboratuvarı Başlatma

Terminalinizi `labs/phase-01-basics-and-isolation` klasöründe açın:

```bash
docker compose up -d
```

Çalışan container'ları listeleyin:
```bash
docker compose ps
```

---

## 🔍 Adım Adım İnceleme ve Canlı Deneyler

### 1. Deney: Ahmet'in Bilgisayarına Giriş ve Kimliğini İnceleme
Alpine Linux container'larında varsayılan kabuk `sh`'tır. Ahmet'in bilgisayarının içine girelim:

```bash
docker exec -it ahmet-pc sh
```

Şimdi ağ kimliğimizi sorgulayalım:
```sh
ip a
```

#### 📋 Çıktının Satır Satır Analizi:
```text
1: lo: <LOOPBACK,UP,LOWER_UP> ...
    inet 127.0.0.1/8 scope host lo
2: eth0@if13: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    link/ether d2:ef:39:55:91:c4 brd ff:ff:ff:ff:ff:ff
    inet 10.10.1.45/24 brd 10.10.1.255 scope global eth0
```

1. **`link/ether d2:ef:39:55:91:c4`**: Ahmet'in sanal ağ kartının benzersiz **fiziksel MAC adresidir** (Kimlik No).
2. **`inet 10.10.1.45/24`**: Ahmet'in mantıksal **IP adresidir** (`10.10.1` mahallesi, no `45`).
3. **`brd 10.10.1.255`**: Bu mahallenin **Broadcast (Megafon)** adresidir. Bu adrese bir seslenilirse odadaki herkes duyar.

---

### 2. Deney: Aynı Odadaki Mehmet'e Ping Atma ve Dedektif ARP'ın Çalışması
Ahmet'in terminalindeyken yan masadaki Mehmet'e ping atalım:

```sh
ping -c 3 10.10.1.46
```

#### 📋 Çıktı:
```text
64 bytes from 10.10.1.46: seq=1 ttl=64 time=0.037 ms
64 bytes from 10.10.1.46: seq=2 ttl=64 time=0.041 ms
3 packets transmitted, 3 received, 0% packet loss
```
Paketler milisaniyenin altında (`0.037 ms`) gidip geldi!

#### 🎬 Arka Planda Milisaniyeler İçinde Ne Yaşandı? (Adım Adım Film Şeridi)
1. **Karar:** Ahmet baktı: *"Hedef IP `10.10.1.46`. Benim maskem `/24`. İkimizin de mahallesi `10.10.1`. Harika, Mehmet benimle aynı odada!"*
2. **Problem:** Ahmet paketi kabloya basacak ama Mehmet'in fiziksel MAC adresini bilmiyor!
3. **Megafon (ARP Request):** Ahmet tüm odaya doğru broadcast fırlattı:  
   📢 *"Hey! 10.10.1.46 IP'sine sahip olan kimse bana derhal fiziksel MAC adresini söylesin!"*
4. **Cevap (ARP Reply):** Mehmet bu sesi duydu ve doğrudan Ahmet'e fısıldadı:  
   🗣️ *"O IP benim! Benim MAC adresim: `76:ae:25:6d:87:95`"*
5. **Kayıt:** Ahmet bu eşleşmeyi unutmamak için cebindeki **not defterine (ARP Tablosuna)** yazdı ve ping paketini fırlattı.

---

### 3. Deney: Ahmet'in Cebindeki Not Defterini Görme (ARP Tablosu)
Ahmet'in hafızasını kontrol edelim:

```sh
ip neigh show
# veya:
arp -a
```

#### 📋 Ekrandaki Çıktı:
```text
10.10.1.46 dev eth0 lladdr 76:ae:25:6d:87:95 STALE
```

* **`10.10.1.46`**: Mehmet'in IP'si.
* **`lladdr 76:ae:25:6d:87:95`**: Mehmet'in Ethernet MAC adresi.
* **`STALE` Ne Anlama Gelir?**  
  İngilizce *"Bayat / Beklemede"* demektir. Linux çekirdeği der ki: *"Ping bitti, Mehmet'le konuşmamızın üzerinden birkaç saniye geçti. Bilgiyi unutmuyorum ama kayıt biraz eskidi. Yeni bir paket gönderirsen anında tekrar `REACHABLE` (Taze) yaparım."*

---

### 4. Deney: Ağ İzolasyonu — Başka Odadaki Muhasebeye Ping Atma
Şimdi Ahmet'in terminalinden `vlan20_sunucu` odasındaki muhasebe makinesine ping atalım:

```sh
ping -c 3 -W 2 10.20.1.50
```

#### 📋 Sonuç:
```text
--- 10.20.1.50 ping statistics ---
3 packets transmitted, 0 packets received, 100% packet loss
```
Paketler **duvara tosladı (%100 kayıp)!**

#### ❓ Neden Ulaşamadı?
1. Ahmet hedef IP'ye baktı: `10.20.1.50`.
2. Kendi maskesine (`/24`) baktı: *"Benim mahallem `10.10.1`, onun mahallesi `10.20.1`. Biz aynı mahallede değiliz!"*
3. Farklı mahallede oldukları için Ahmet odaya *"10.20.1.50 kimde?"* diye bağıramaz; çünkü sanal köprü bu anonsu diğer odaya geçirmez.
4. Paketi kapıdaki yönlendiriciye (**Default Gateway / Router**) vermesi gerekir.
5. Ancak `vlan10_personel` ile `vlan20_sunucu` odaları arasında paket taşıyacak **hiçbir yönlendirici (Router) kablosu tanımlı değildir!**
6. Docker bu iki odayı birbirinden tamamen yalıtır. İşte buna **Katman 2 Ağ İzolasyonu (Network Isolation)** denir.

---

## 🚪 Çıkış ve Temizlik

Ahmet'in container'ından çıkmak için:
```sh
exit
```

Laboratuvarı tamamen kapatmak için:
```bash
docker compose down
```

---

## 🎯 Bu Fazda Cebimize Ne Koyduk?
1. **VLAN / Bridge Ağı:** Aynı sunucu üzerinde birbirinden tamamen bağımsız ve izole odalar kurmayı,
2. **Subnet Mask (`/24`):** Cihazın kiminle aynı odada, kiminle farklı mahallede olduğunu nasıl anladığını,
3. **MAC vs IP:** IP'nin geçici posta adresi, MAC'in ise kalıcı T.C. kimlik numarası olduğunu,
4. **ARP Protokolü:** Bilgisayarların IP'den donanım kimliğini nasıl keşfettiğini ve hafızasında tuttuğunu öğrendik.

Aradaki duvarı yıkıp iki odayı bir yönlendirici (Router) ile konuşturacağımız [**Faz 2: Yönlendirme (Routing) & Inter-VLAN Gateway**](../phase-02-routing-and-gateway/) laboratuvarına hazırsınız! 🚀
