# 🔬 Faz 1: Ağ Temelleri, Alt Ağlar & İzolasyon (Subnets & Isolation)

Bu laboratuvarda; bilgisayar ağlarının en temel yapı taşları olan **MAC adresi**, **IP adresi**, **Subnet Mask (/24)**, **ARP (Adres Çözümleme Protokolü)** ve **Katman 2 Sanal Ağ İzolasyonu** mekanizmalarını Docker üzerinde canlı olarak inceleyeceksiniz.

---

## 📌 Teorik Bağlantı (Ana Rehber)
Bu lab aşağıdaki rehber bölümlerini uygulamaya döker:
* [Modül 1 / Madde 1: MAC Adresi (Donanım Kimliği)](../../README.md#1-mac-adresi-media-access-control)
* [Modül 1 / Madde 2: IP Adresi (Mantıksal Adresleme)](../../README.md#2-ip-adresi-ipv4--ipv6)
* [Modül 1 / Madde 3: Subnet Mask & CIDR (/24 Mantığı)](../../README.md#3-subnet-mask-alt-ağ-maskesi--cidr)
* [Modül 2 / Madde 5: ARP Protokolü & Karar Mekanizması](../../README.md#5-arp-address-resolution-protocol)

---

## 🏗️ Laboratuvar Mimarisi

```text
       [ vlan10_personel Köprüsü (10.10.1.0/24) ]
             │                              │
             ▼                              ▼
     [ ahmet-pc ]                    [ mehmet-pc ]
    (10.10.1.45)                    (10.10.1.46)
          │
          │ ❌ (Farklı Alt Ağ - Doğrudan İletişim Yok / İzolasyon)
          ▼
 [ vlan20_sunucu Köprüsü (10.20.1.0/24) ]
             │
             ▼
    [ gizli-muhasebe ]
      (10.20.1.50)
```

---

## 🚀 Laboratuvarı Başlatma

Terminalinizi bu klasörde (`labs/phase-01-basics-and-isolation`) açın ve container'ları ayağa kaldırın:

```bash
docker compose up -d
```

Container'ların durumunu kontrol edin:
```bash
docker compose ps
```

---

## 🔍 Adım Adım İnceleme ve Deneyler

### 1. Adım: Cihazın IP ve MAC Adreslerini Görme
Ahmet'in bilgisayarının terminaline bağlanıp ağ arayüzünü inceleyelim:

```bash
docker exec -it ahmet-pc ip -c a
```

#### 📋 Örnek Çıktı ve Yorumu:
```text
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN ...
    inet 127.0.0.1/8 scope host lo
2: eth0@if12: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    link/ether 02:42:0a:0a:01:2d brd ff:ff:ff:ff:ff:ff
    inet 10.10.1.45/24 brd 10.10.1.255 scope global eth0
```

* **`link/ether 02:42:0a:0a:01:2d`**: Cihazın sanal ağ kartının **MAC adresidir** (Katman 2 donanım kimliği).
* **`inet 10.10.1.45/24`**: Cihaza atanan **IPv4 adresidir** (Katman 3).
* **`/24`**: Subnet mask'tır (`255.255.255.0`). İlk 24 bit kilitlidir (`10.10.1.x` mahalle/ağ adıdır), son 8 bit cihaz numarasıdır (`.45`).
* **`brd 10.10.1.255`**: Bu alt ağın **Broadcast (Megafon)** adresidir.

---

### 2. Adım: Docker Bridge (Sanal Switch) Yapısını İnceleme
Docker bu ağı kendi içinde bir Linux Bridge olarak yönetir. Dışarıdan ağın detaylarına bakalım:

```bash
docker network inspect vlan10_personel
```

* Çıktıda `Subnet: 10.10.1.0/24`, `Gateway: 10.10.1.1` ve bu ağa bağlı olan `ahmet-pc` ile `mehmet-pc` container'larının listesini görebilirsiniz.

---

### 3. Adım: Aynı Alt Ağda İletişim ve ARP Tablosunu İnceleme
Ahmet, aynı ağdaki çalışma arkadaşı Mehmet'e (`10.10.1.46`) ping atsın:

```bash
docker exec -it ahmet-pc ping -c 3 10.10.1.46
```

Paketler başarıyla iletilir! Peki Ahmet, Mehmet'in fiziksel MAC adresini nasıl öğrendi?  
Hemen Ahmet'in **ARP önbelleğine (ARP Cache)** bakalım:

```bash
docker exec -it ahmet-pc ip neigh show
# veya:
docker exec -it ahmet-pc arp -a
```

#### 📋 Örnek Çıktı:
```text
10.10.1.46 dev eth0 lladdr 02:42:0a:0a:01:2e REACHABLE
```

💡 **Ne Oldu?**
1. Ahmet ilk ping paketini atmadan önce kendi hafızasına baktı: *"Mehmet'in IP'si 10.10.1.46 ama MAC adresini bilmiyorum!"*
2. Ağa bir **ARP Request (Broadcast)** fırlattı: *"Kimde 10.10.1.46 varsa bana MAC adresini söylesin!"*
3. Mehmet bu çağrıyı duydu ve kendi MAC adresini (`02:42:0a:0a:01:2e`) Ahmet'e bildirdi.
4. Ahmet bu bilgiyi hafızasına (ARP Tablosu) kaydetti ve artık paketler doğrudan iletildi.

---

### 4. Adım: Alt Ağ İzolasyonu (Farklı Ağa Ulaşamama Durumu)
Şimdi Ahmet, diğer alt ağdaki muhasebe sunucusuna (`10.20.1.50`) ping atmayı denesin:

```bash
docker exec -it ahmet-pc ping -c 3 -W 2 10.20.1.50
```

#### 📋 Sonuç:
Paketler **ulaşmaz (%100 packet loss)** veya zaman aşımına uğrar!

#### ❓ Neden Ulaşamadı?
1. Ahmet hedef IP olan `10.20.1.50` ile kendi Subnet Mask'ını (`/24`) karşılaştırdı.
2. `10.20.1.x` mahallesinin, kendi mahallesi olan `10.10.1.x` ile **aynı olmadığını** anladı.
3. Kendi ağında doğrudan ARP ile bu cihazı bulamayacağını bildiği için paketi varsayılan ağ geçidine teslim etmeye çalıştı.
4. Ancak `vlan10_personel` köprüsü ile `vlan20_sunucu` köprüsü arasında paket taşıyacak bir yönlendirici (Router) veya aracı köprü tanımlı değildir! Docker bu iki ağı birbirinden tamamen izole tutar.

---

## 🧹 Laboratuvarı Kapatma ve Temizlik

Deneyleri tamamladıktan sonra laboratuvar ortamını temizlemek için:

```bash
docker compose down
```

---

## 🎯 Bu Fazda Ne Öğrendik?
1. Bir cihazın ağdaki fiziksel kimliğinin (**MAC**) ve mantıksal kimliğinin (**IP**) farkını,
2. Aynı alt ağdaki cihazların **ARP** sayesinde birbirlerinin MAC adresini bularak doğrudan haberleştiğini,
3. Farklı alt ağların ve Docker bridge ağlarının varsayılan olarak **izole** olduğunu ve aralarında bir Router olmadan birbirlerine paket geçiremeyeceğini.

Bir sonraki aşama olan [**Faz 2: Yönlendirme (Routing) & Inter-VLAN Gateway**](../phase-02-routing-and-gateway/) ile bu iki ağ arasına bir yönlendirici koyup iletişimi sağlayacağız! 🚀
