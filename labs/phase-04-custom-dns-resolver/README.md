# 🔍 Faz 4: Şirket İçi Özel DNS Çözümleme (CoreDNS ile `sirket.local`)

Ana rehberimizin 6. modülünde yer alan şu soruya dönelim:  
> *"Ahmet tarayıcısına `portal.sirket.local` yazdığında bilgisayarı bu alan adının sistem odasındaki `10.20.1.50` olduğunu nereden biliyor?"*

Bu laboratuvarda; kurumsal yapılarda ve Kubernetes altyapılarında standart olan **CoreDNS** sunucusunu ayağa kaldıracak, özel şirket bölgemizi (`zone: sirket.local`) tanımlayacak ve **`dig`** ile DNS protokolünün nasıl çalıştığını adım adım analiz edeceğiz.

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
