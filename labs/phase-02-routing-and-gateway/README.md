# 🧭 Faz 2: Yönlendirme (Routing), Default Gateway & Inter-VLAN İletişim

Faz 1'de iki farklı alt ağın (`vlan10` ve `vlan20`) birbirinden tamamen izole olduğunu ve doğrudan konuşamadığını gördük. Bu laboratuvarda; araya çift ağ kartına (vNIC) sahip bir **Linux Core Router** yerleştirecek, **IP Yönlendirme (IP Forwarding)** mekanizmasını aktif edecek ve paketlerin ağlar arasında sekerek hedefe nasıl ulaştığını **Traceroute** ile adım adım izleyeceğiz.

![Inter-VLAN Yönlendirme ve Çift Ağ Kartlı Linux Core Router Mimarisi](../../assets/inter_vlan_routing.jpg)

---

## 📌 Teorik Bağlantı (Ana Rehber)
Bu lab aşağıdaki rehber bölümlerini uygulamaya döker:
* [Modül 1 / Madde 4: Default Gateway (Varsayılan Ağ Geçidi)](../../README.md#4-default-gateway-varsayılan-ağ-geçidi)
* [Modül 4 / Madde 11: VLAN & Inter-VLAN Routing](../../README.md#11-vlan-virtual-local-area-network--trunking)
* [Modül 6: Adım Adım Temel Akış (Departmanlar Arası Geçiş)](../../README.md#3-aşama-departmanlar-arası-geçiş-ve-güvenlik-duvarı-inter-vlan-routing--firewall)

---

## 🏗️ Laboratuvar Mimarisi

```text
[ ahmet-pc ] (10.10.1.45)
     │  (vlan10_personel)
     ▼
[ core-router ]
  ├── eth0: 10.10.1.254 (Personel Ağı Kapısı)
  └── eth1: 10.20.1.254 (Sunucu Ağı Kapısı)
     │  (vlan20_sunucu)
     ▼
[ gizli-muhasebe ] (10.20.1.50)
```

---

## 🚀 Laboratuvarı Başlatma

Terminalinizi bu klasörde (`labs/phase-02-routing-and-gateway`) açın ve container'ları ayağa kaldırın:

```bash
docker compose up -d
```

---

## 🔍 Adım Adım İnceleme ve Deneyler

### 1. Adım: Router'ın Çift Ağ Kartını ve Yönlendirme Tablosunu İnceleme
Core Router her iki ağa da fiziksel olarak bağlıdır. Arayüzlerine bakalım:

```bash
docker exec -it core-router ip -c a
```

* `eth0`: `10.10.1.254/24` (Ahmet'in ağındaki bacağı)
* `eth1`: `10.20.1.254/24` (Muhasebe ağındaki bacağı)

Şimdi Router'ın çekirdeğindeki **IP İleri Taşıma (IP Forwarding)** bayrağının açık olduğunu doğrulayalım:

```bash
docker exec -it core-router cat /proc/sys/net/ipv4/ip_forward
```
*(Sonuç `1` olmalıdır. Bu, Linux çekirdeğine "Gelen paket sana ait değilse bile atma, diğer arayüzden hedefe fırlat" emrini verir).*

---

### 2. Adım: İstemcilere Ağ Geçidi (Route) Tanımlama
Ahmet'in bilgisayarı henüz `10.20.1.0/24` ağına gitmek için kime başvuracağını bilmez. Ahmet'in rotasını inceleyelim:

```bash
docker exec -it ahmet-pc ip route show
```

Şimdi Ahmet'e şu kuralı söyleyelim:  
*"Eğer `10.20.1.0/24` (Sunucu) ağına bir paket göndermek istersen, bunu kapıdaki Core Router'a (`10.10.1.254`) teslim et!"*

```bash
docker exec -it ahmet-pc ip route add 10.20.1.0/24 via 10.10.1.254
```

Aynı şekilde yanıt paketinin Ahmet'e dönebilmesi için muhasebe sunucusuna da dönüş yolunu ekleyelim:
```bash
docker exec -it gizli-muhasebe ip route add 10.10.1.0/24 via 10.20.1.254
```

---

### 3. Adım: Canlı Ping Testi (Duvar Yıkıldı!)
Şimdi Ahmet tekrar muhasebe sunucusuna ping atsın:

```bash
docker exec -it ahmet-pc ping -c 3 10.20.1.50
```

#### 📋 Sonuç:
```text
64 bytes from 10.20.1.50: seq=1 ttl=63 time=0.124 ms
64 bytes from 10.20.1.50: seq=2 ttl=63 time=0.089 ms
```
🎉 **Başarılı!** Paketler artık iki farklı mahalle arasında sorunsuzca akmaktadır!  
*(Dikkat: `ttl=63` oldu! Normalde TTL 64 başlar; Router üzerinden geçtiği için 1 azaldı).*

---

### 4. Adım: Paketlerin Yolunu İzleme (Traceroute)
Paketin router üzerinden sektiğini kendi gözlerimizle görelim:

```bash
docker exec -it ahmet-pc traceroute -n 10.20.1.50
```

#### 📋 Örnek Çıktı:
```text
traceroute to 10.20.1.50 (10.20.1.50), 30 hops max, 46 byte packets
 1  10.10.1.254  0.021 ms  0.012 ms  0.011 ms   <--- 1. Sekme: CORE ROUTER
 2  10.20.1.50   0.034 ms  0.027 ms  0.021 ms   <--- 2. Sekme: HEDEF SUNUCU
```

---

### 5. Adım: "Kabloyu Kesmek" — IP Forwarding Kapatma Deneyi
Bir yönlendiricinin paketleri nasıl anında kestiğini görmek için Core Router üzerinde çekirdek yönlendirmesini sıfırlayalım:

```bash
docker exec -it core-router sysctl -w net.ipv4.ip_forward=0
```

Şimdi Ahmet tekrar ping atsın:
```bash
docker exec -it ahmet-pc ping -c 2 -W 2 10.20.1.50
```
*(Paketler anında düşer ve `%100 packet loss` olur!)*

Geri açmak için:
```bash
docker exec -it core-router sysctl -w net.ipv4.ip_forward=1
```
*(Ping anında tekrar akmaya başlar!)*

---

## 🧹 Laboratuvarı Kapatma ve Temizlik

```bash
docker compose down
```

---

## 🎯 Bu Fazda Ne Öğrendik?
1. **Default Gateway / Route** olmadan cihazların kendi alt ağları dışındaki hedeflere paket ulaştıramayacağını,
2. Çoklu arayüze sahip bir cihazın işletim sistemi çekirdeğindeki **`ip_forward`** mekanizmasıyla nasıl tam teşekküllü bir yönlendiriciye (Router) dönüştüğünü,
3. **Traceroute** ile paketin ağ geçitlerinden geçerken TTL değerinin düşüşünü ve sekmelerini adım adım izlemeyi.

Sıradaki laboratuvarımız: [**Faz 3: Docker NAT ve Port Eşleme (DNAT / SNAT)**](../phase-03-nat-and-port-mapping/)! 🚀
