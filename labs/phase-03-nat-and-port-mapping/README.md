# 🔄 Faz 3: Docker Ağ Çevirisi (NAT: DNAT & SNAT) ve Port Eşleme

Her gün kullandığımız `docker run -p 8080:80` veya `ports: - "8080:80"` komutunun arka planda Linux çekirdeğinde ve ağ katmanında gerçekte **ne yaptığını** hiç merak ettiniz mi?

Bu laboratuvarda; Docker'ın port yayını yaparken **DNAT (Destination NAT)** ve container'ları internete çıkarırken **SNAT (Source NAT / Masquerade)** tekniklerini `iptables` ile nasıl kurduğunu adım adım inceleyeceğiz.

---

## 📌 Teorik Bağlantı (Ana Rehber)
Bu lab aşağıdaki rehber bölümlerini uygulamaya döker:
* [Modül 4 / Madde 10: NAT (Network Address Translation)](../../README.md#10-nat-network-address-translation)
* [Modül 3 / Madde 9: Portlar ve Sockets](../../README.md#9-portlar-ve-sockets)

---

## 🏗️ Laboratuvar Mimarisi & Paket Yolculuğu

```text
[ Tarayıcı / İstemci ] 
       │ 
       ▼ İstek: localhost:8080 (Hedef: Host IP:8080)
┌────────────────────────────────────────────────────────┐
│ ANA MAKİNE (HOST)                                      │
│                                                        │
│  [ Linux iptables: PREROUTING / DOCKER Zinciri ]       │
│  ==> DNAT Kuralı: "8080'e geleni 172.28.0.10:80 yap!"  │
│                                                        │
│         │                                              │
│         ▼ Yeniden Yazılan Paket: 172.28.0.10:80        │
│  [ Docker Bridge: nat_lab_net ]                        │
│         │                                              │
│         ▼                                              │
│  [ web-service Container'ı ] (Nginx Port 80)           │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Laboratuvarı Başlatma

Terminalinizi bu klasörde (`labs/phase-03-nat-and-port-mapping`) açın:

```bash
docker compose up -d
```

Servisin çalıştığını test edin:
```bash
curl http://localhost:8080
```
*(Nginx karşılama HTML sayfasını görmelisiniz).*

---

## 🔍 Adım Adım İnceleme ve Deneyler

### 1. Adım: DNAT (Destination NAT) Nedir ve Nereden Bakılır?
Dış dünyadan ana makinenizin `8080` portuna gelen paket, kapalı bir kutu olan container'ın içindeki `172.28.0.10:80` soketine nasıl ulaştı?

Bunu yapan mekanizma **DNAT (Hedef NAT)**'tır. Linux işletim sistemindeki NAT kurallarını listeleyelim:

*(Linux veya WSL2 terminalinde):*
```bash
sudo iptables -t nat -L DOCKER -n -v
```

#### 📋 Örnek Çıktı ve Analizi:
```text
Chain DOCKER (2 references)
 pkts bytes target     prot opt in     out     source               destination         
    5   300 DNAT       tcp  --  !br-xx *       0.0.0.0/0            0.0.0.0/0            tcp dpt:8080 to:172.28.0.10:80
```

* **`target: DNAT`**: Paketin başlığındaki "Hedef IP ve Port" değiştirilecektir.
* **`tcp dpt:8080`**: Eğer gelen istek TCP ve hedef port `8080` ise,
* **`to:172.28.0.10:80`**: Paketin hedef adresini anında container'ın özel IP'si olan `172.28.0.10:80` olarak güncelle!

Böylece paket çekirdek seviyesinde container'ın içine saptırılır.

---

### 2. Adım: SNAT (Source NAT / Masquerade) Nedir?
Peki container internetteki bir sunucuya (örneğin `curl https://google.com` veya `ping 1.1.1.1`) istek attığında ne olur?

1. Container'ın IP'si `172.28.0.10`'dur. Bu bir **RFC 1918 Private (Özel) IP**'sidir.
2. Bu IP ile doğrudan genel internette gezinemezsiniz (çünkü internet router'ları bu IP'ye dönüş yolunu bilemez ve paketi çöpe atar).
3. Burada devreye **SNAT (Masquerade)** girer!

Linux'taki `POSTROUTING` zincirine bakalım:
```bash
sudo iptables -t nat -L POSTROUTING -n -v
```

#### 📋 Örnek Çıktı:
```text
Chain POSTROUTING (policy ACCEPT 15 packets, 952 bytes)
 pkts bytes target     prot opt in     out     source               destination         
   42  2520 MASQUERADE all  --  *      eth0    172.28.0.0/16        0.0.0.0/0
```

* **`target: MASQUERADE`**: Kaynak adres gizleme (PAT / Dynamic SNAT).
* **`source: 172.28.0.0/16`**: Container ağından çıkan tüm paketlerin üzerindeki kaynak IP silinir; yerine **ana makinenin gerçek IP'si** yazılır!
* Google cevabı ana makineye döndüğünde, Linux çekirdeğindeki bağlantı takip tablosu (**conntrack**) paketin `curler` container'ına ait olduğunu hatırlar ve cevabı içeri teslim eder.

---

### 3. Adım: `docker-proxy` Süreci Nedir?
Docker sadece `iptables` ile yetinmez; `iptables` desteklemeyen veya localhost üzerinden gelen bazı durumlar için kullanıcı alanında (User-space) çalışan küçük bir vekil süreç başlatır:

```bash
ps aux | grep docker-proxy
# Windows PowerShell için:
Get-Process | Where-Object { $_.ProcessName -like "*docker-proxy*" }
```

Görüleceği üzere `docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8080 -container-ip 172.28.0.10 -container-port 80` şeklinde bir işlem arka planda çalışmaktadır.

---

## 🧹 Laboratuvarı Kapatma ve Temizlik

```bash
docker compose down
```

---

## 🎯 Bu Fazda Ne Öğrendik?
1. `docker run -p` komutunun aslında arka planda bir **DNAT (Destination NAT)** kuralı oluşturduğunu,
2. Container'ların internete çıkarken IP adreslerinin **SNAT (MASQUERADE)** ile ana makinenin IP'sine dönüştürüldüğünü,
3. `iptables -t nat` tablosunun bu çeviri zincirlerini nasıl işlettiğini.

Sıradaki laboratuvarımız: [**Faz 4: Şirket İçi Özel DNS Çözümleme (CoreDNS)**](../phase-04-custom-dns-resolver/)! 🚀
