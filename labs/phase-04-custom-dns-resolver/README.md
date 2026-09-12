# 🔍 Faz 4: Şirket İçi Özel DNS Çözümleme (CoreDNS ile `sirket.local`)

Ana rehberimizin 6. modülünde yer alan şu soruya dönelim:  
> *"Ahmet tarayıcısına `portal.sirket.local` yazdığında bilgisayarı bu alan adının sistem odasındaki `10.20.1.50` olduğunu nereden biliyor?"*

Bu laboratuvarda; kurumsal yapılarda ve Kubernetes altyapılarında standart olan **CoreDNS** sunucusunu ayağa kaldıracak, özel şirket bölgemizi (`zone: sirket.local`) tanımlayacak ve **`dig`** ile DNS protokolünün nasıl çalıştığını adım adım analiz edeceğiz.

---

## ❓ 1. Özel Şirket DNS Bölgesi (Private Zone) Neden Kurulur?

Neden `google.com` gibi genel alan adlarıyla yetinmeyip şirket içinde `sirket.local`, `corp.internal` gibi **özel (Private) bir DNS bölgesi** kurarız?

### 🛡️ A. Güvenlik ve Gizlilik (Saldırı Yüzeyini Daraltma):
* Şirket içinde `muhasebe.sirket.local`, `gitlab.sirket.local`, `veritabani.sirket.local` gibi onlarca hassas servis çalışır.
* Bu sunucuların IP adreslerini genel internetteki DNS sunucularına (Cloudflare, Google vb.) yazamazsınız!
* Eğer yazsaydınız; internetteki herhangi bir hacker veya bot, şirketinizin tüm iç sunucu adlarını ve IP haritasını (`10.20.1.x`) birkaç saniyede ifşa edebilirdi. Özel DNS bölgesi sayesinde şirket haritası **yalnızca ofis duvarlarının içinde kalır**.

### 🏢 B. Özel IP (RFC 1918) Standartları:
* `10.0.0.0/8`, `172.16.0.0/12` ve `192.168.0.0/16` blokları internette yönlendirilemeyen özel adreslerdir.
* Genel internet DNS sunucuları bu IP'ler için gelen sorguları ciddiye almaz veya çözümlemez. Bu adresleri sadece kurumun kendi iç DNS sunucusu bilir ve eşleştirir.

### 🌐 C. İnternet Kesilse Bile Şirket Çalışmaya Devam Eder (İş Sürekliliği):
* Şirketin Türk Telekom veya fiber internet hattı kopsa dahi; ofis içindeki çalışanlar şirket portalına, dosya sunucularına ve muhasebeye **kesintisiz erişmeye devam eder**. Çünkü DNS sorguları dış dünyaya çıkmadan yerel sistem odasındaki CoreDNS'ten 0 milisaniyede cevaplanır.

### 🔄 D. Sunucu Taşınsa Bile Çalışanlar Etkilenmez:
* Ahmet'e *"Muhasebe için 10.20.1.50 adresine gir"* derseniz yarın sunucu değişip `10.20.1.99` olduğunda 500 çalışana tek tek yeni IP ezberletmeniz gerekir.
* Oysa herkes `portal.sirket.local` yazar. IT uzmanı sadece DNS sunucusundaki tek bir A kaydını günceller; 500 çalışanın haberi bile olmadan sistem kesintisiz çalışır.

### 🌗 E. Split-Horizon (Bölünmüş Ufuk) DNS:
* Şirketin sitesi `sirket.com` olsun.
* Ahmet ofis masasındayken `sirket.com` yazdığında yerel DNS onu doğrudan iç ağdaki yerel IP'ye (`10.20.1.50`) yönlendirir (hızlı ve kotasız).
* Ahmet akşam evine gidip internetten `sirket.com` yazdığında ise genel DNS onu şirketin dış Public IP'sine (`212.x.x.x`) yönlendirir.

---

## ⚙️ 2. Bir DNS Sunucusunun İçinde Hangi İşlemler Yapılır?

Bir DNS sunucusu sadece bir telefon rehberi değildir; içinde şu 6 kritik motoru çalıştırır:

```text
               ┌────────────────────────────────────────────────────────┐
               │              ŞİRKET İÇİ DNS SUNUCUSU                   │
               │                                                        │
İstemci Sorgusu│ 1. [YETKİLİ BÖLGE (Authoritative)]: sirket.local mi?   │
──────────────►│    ├── EVET: Kendi kayıtlarımdan dön (10.20.1.50)      │
(UDP Port 53)  │    └── HAYIR: Dış dünyaya ait bir alan adı mı?         │
               │                                                        │
               │ 2. [ÖNBELLEK (Cache)]: Yakın zamanda soruldu mu?       │
               │    ├── EVET: RAM'deki önbellekten 0 ms'de teslim et    │
               │    └── HAYIR: 3. motora aktar                          │
               │                                                        │
               │ 3. [İLETİCİ (Forwarder)]: 1.1.1.1 / 8.8.8.8'e git     │
               │    └── İnternetten cevabı al, önbelleğe yaz, ilet      │
               │                                                        │
               │ 4. [GÜVENLİK / SİNKHOLE]: Zararlı / Yasaklı site mi?   │
               │    └── EVET ise: 0.0.0.0 dön ve engelle!               │
               └────────────────────────────────────────────────────────┘
```

1. **Yetkili Çözümleme (Authoritative Zone):** Kendi sorumlu olduğu bölgedeki (`sirket.local`) kayıtların kesin ve tartışmasız sahibidir (A, CNAME, MX, TXT kayıtları).
2. **Önbellekleme (Caching & TTL):** Bir sorguyu çözdükten sonra sonucu RAM'inde tutar. Bir sonraki kullanıcı aynı adresi istediğinde tekrar diske veya dış internete sormadan anında döner.
3. **Yönlendirme / İletim (Forwarding / Recursion):** Kendi bilmediği genel domain'leri (`google.com`, `github.com`) internetteki genel DNS sunucularına (`1.1.1.1`, `8.8.8.8`) paslayarak sonucu istemciye ulaştırır.
4. **Ters Çözümleme (Reverse DNS / PTR Kaydı):** IP adresinden alan adını bulur (`10.20.1.50` kimdir? $\rightarrow$ `portal.sirket.local`).
5. **DNS Tabanlı Yük Dengeleme (Round-Robin):** Bir alan adına 2 ayrı IP yazılırsa (örn: `10.20.1.51` ve `10.20.1.52`), DNS sunucusu her sorana sırayla birini dönerek yükü dengeler.
6. **Güvenlik Filtreleme (DNS Sinkholing / Pi-hole Mantığı):** Kurum içi cihazların virüslü veya zararlı sitelere gitmesini engellemek için kara listedeki domain'lere sahte `0.0.0.0` IP'si dönerek bağlantıyı keser.

---

## 📜 3. Bizim Laboratuvar Yapılandırmamız Bu Çarkları Nasıl Çeviriyor?

Laboratuvarımızdaki iki yapılandırma dosyası bu motorları şöyle devreye sokar:

### A. `Corefile` (CoreDNS'in Beyni):
```text
sirket.local:53 {
    file /etc/coredns/db.sirket.local   <-- 1. MOTOR: Yetkili bölge dosyasını oku
    log                                 <-- Gelen tüm UDP 53 sorgularını konsola yaz
    errors
}

.:53 {
    forward . 1.1.1.1 8.8.8.8          <-- 3. MOTOR: Şirket dışı sorguları internete pasla
    cache 30                            <-- 2. MOTOR: Yanıtları 30 saniye boyunca RAM'de sakla
    log
    errors
}
```

### B. `db.sirket.local` (Bölge Veritabanı):
* **`SOA` (Start of Authority):** Bu bölgenin yetki kimliğidir.
* **`portal IN A 10.20.1.50`:** Doğrudan isim $\rightarrow$ IP eşleştirmesidir (A Kaydı).
* **`api IN CNAME portal.sirket.local.`:** Takma ad eşleştirmesidir (CNAME Kaydı). `api` adresine gelenler otomatik olarak `portal`'ın IP'sine yönlendirilir.

---

## 📌 Teorik Bağlantı (Ana Rehber)
Bu lab aşağıdaki rehber bölümlerini uygulamaya döker:
* [Modül 2 / Madde 7: DNS (Domain Name System)](../../README.md#7-dns-domain-name-system)
* [Modül 6 / 2. Aşama: "portal.sirket.local Nerede?" (Şirket İçi DNS Çözümleme)](../../README.md#2-aşama-portalsirketlocal-nerede-şirket-içi-dns-çözümleme)

---

## 🏗️ Laboratuvar Mimarisi

```text
[ ahmet-pc ] (10.20.1.45)
     │
     │ 1. DNS Sorgusu: "portal.sirket.local kimdir?" (Port 53 UDP)
     ▼
[ company-dns (CoreDNS) ] (10.20.1.10)
  ├── sirket.local Bölgesi:
  │     ├── portal.sirket.local   ──► 10.20.1.50 (A Kaydı)
  │     ├── muhasebe.sirket.local ──► 10.20.1.50 (A Kaydı)
  │     └── api.sirket.local      ──► portal (CNAME)
  │
  └── Diğer Tüm Alan Adları (google.com vb.):
        └── Forwarder ──► 1.1.1.1 & 8.8.8.8
```

---

## 🚀 Laboratuvarı Başlatma

Terminalinizi bu klasörde (`labs/phase-04-custom-dns-resolver`) açın:

```bash
docker compose up -d
```

CoreDNS'in sağlıklı açıldığını kontrol edin:
```bash
docker compose logs company-dns
```
*(Ekranda `CoreDNS-x.x.x linux/amd64` ve `plugin/reload` mesajlarını görmelisiniz).*

---

## 🔍 Adım Adım İnceleme ve Deneyler

### 1. Adım: İstemcinin DNS Ayarlarına Bakma (`/etc/resolv.conf`)
Ahmet'in bilgisayarı internetteki isimleri sormak için hangi DNS sunucusuna gideceğini nereden bilir?

```bash
docker exec -it ahmet-pc cat /etc/resolv.conf
```

#### 📋 Çıktı:
```text
nameserver 10.20.1.10
```
Ahmet'in sistemine şirket içi CoreDNS sunucumuz (`10.20.1.10`) birincil isim sunucusu olarak tanıtılmıştır.

---

### 2. Adım: `dig` ile Şirket İçi A Kaydını Sorgulama
Ahmet terminalinden şirket portalının adresini sorgulasın:

```bash
docker exec -it ahmet-pc dig portal.sirket.local
```

#### 📋 Örnek Çıktı ve Derinlemesine Analiz:
```text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 38241
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 1, ADDITIONAL: 2

;; QUESTION SECTION:
;portal.sirket.local.           IN      A

;; ANSWER SECTION:
portal.sirket.local.    3600    IN      A       10.20.1.50

;; Query time: 0 msec
;; SERVER: 10.20.1.10#53(10.20.1.10)
```

* **`status: NOERROR`**: Alan adı başarıyla bulundu (Eğer yanlış yazsaydık `NXDOMAIN` dönerdi).
* **`flags: aa` (Authoritative Answer)**: Bu cevap yetkili sunucudan (CoreDNS) geldi; tahmin veya rastgele önbellek değil.
* **`ANSWER SECTION`**: `portal.sirket.local` $\rightarrow$ `10.20.1.50` (A Kaydı).
* **`3600`**: Kaydın **TTL (Time-To-Live)** süresidir (saniye cinsinden geçerlilik).
* **`SERVER: 10.20.1.10#53`**: Yanıtın CoreDNS'in **UDP 53** portundan alındığını teyit eder.

---

### 3. Adım: CNAME (Takma Ad / Alias) Kaydını İnceleme
Şimdi `api.sirket.local` adresini sorgulayalım:

```bash
docker exec -it ahmet-pc dig api.sirket.local
```

#### 📋 Çıktı:
```text
;; ANSWER SECTION:
api.sirket.local.       3600    IN      CNAME   portal.sirket.local.
portal.sirket.local.    3600    IN      A       10.20.1.50
```
DNS sunucusu zinciri otomatik takip etti:  
`api` $\longrightarrow$ `portal` (CNAME) $\longrightarrow$ `10.20.1.50` (A).

---

### 4. Adım: Dış İnternet Sorgusu (Recursive Forwarding)
CoreDNS yalnızca şirket içi kayıtları tutmaz; şirket dışı istekleri internet omurgasına yönlendirir (Recursive DNS):

```bash
docker exec -it ahmet-pc nslookup google.com
```

Ahmet'in `google.com` adresini de CoreDNS üzerinden başarıyla çözdüğünü görebilirsiniz.

---

### 5. Adım: CoreDNS Loglarını Canlı İzleme
Yeni bir terminal sekmesinde CoreDNS loglarını açın:

```bash
docker compose logs -f company-dns
```

Ardından Ahmet'in terminalinden `ping portal.sirket.local` veya `dig test.sirket.local` çalıştırın. CoreDNS konsolunda gelen her bir UDP 53 paketinin IP'si, türü ve yanıt süresi canlı olarak akacaktır!

---

## 🧹 Laboratuvarı Kapatma ve Temizlik

```bash
docker compose down
```

---

## 🎯 Bu Fazda Ne Öğrendik?
1. Alan adlarının IP adreslerine nasıl çevrildiğini (**A Kaydı**),
2. **CNAME** kayıtlarının nasıl takma ad olarak çalıştığını,
3. Bir istemcinin `/etc/resolv.conf` dosyası üzerinden DNS sunucusuyla **Port 53 UDP** ile nasıl el sıkıştığını ve `dig` komut çıktılarının nasıl okunacağını.

Sıradaki laboratuvarımız: [**Faz 5: Katman 7 Yük Dengeleme, Reverse Proxy & SSL (Nginx)**](../phase-05-reverse-proxy-cluster/)! 🚀
