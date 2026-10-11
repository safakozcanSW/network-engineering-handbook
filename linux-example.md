# 🐧 Linux Üzerinde Ağ İstek Akışını Adım Adım İnceleme ve Test Rehberi (linux-example.md)

Bu kılavuz, [OZET.md](OZET.md) dosyasında anlatılan 15 aşamalı kronolojik ağ yaşam döngüsünü **gerçek bir Linux işletim sistemi üzerinde** (Ubuntu, Debian, RHEL, CentOS, WSL2 veya Docker konteyneri) adım adım komutlarla incelemenizi, doğrulamanızı ve test etmenizi sağlar.

---

## 📑 Adım Adım Komut Haritası

| Aşama | Konu | İlgili Linux Komutu / Araç | Neyi Doğruluyoruz? |
| :---: | :--- | :--- | :--- |
| **01** | **MAC Adresi** | `ip link show` | Donanımsal 48-bit fiziksel ağ kartı adresi (NIC) |
| **02** | **DHCP (DORA)** | `journalctl -u NetworkManager` / `dhclient` | IP, maske ve gateway alma sürecinin logları |
| **03** | **IP Adresi** | `ip -br addr show` | Katman 3 mantıksal IPv4 ve IPv6 adresleri |
| **04** | **Subnet Mask & CIDR** | `ip -4 addr show eth0` / `ipcalc` | Ağ sınırı (/24), Network ve Broadcast adresi |
| **05** | **Default Gateway** | `ip route show default` | Dış dünyaya çıkış kapısı (Router IP'si) |
| **06** | **ARP** | `ip neigh show` / `arping` | Gateway veya komşu IP'nin fiziksel MAC eşlemesi |
| **07** | **DNS** | `dig google.com` / `resolvectl` | Alan adının sayısal IP adresine çözümlenmesi |
| **08** | **Port & Socket** | `ss -tulpn` / `ss -tan` | Açık portlar, dinlenen servisler ve `IP:Port` soketleri |
| **09** | **TCP & UDP** | `tcpdump` / `curl` | TCP 3-Way Handshake (`SYN, SYN-ACK, ACK`) yakalama |
| **10** | **Firewall** | `iptables -L -v -n` / `conntrack` | Paket denetim kuralları ve durum tablosu (*Stateful*) |
| **11** | **NAT (PAT/SNAT)** | `iptables -t nat -L` / `curl icanhazip.com` | Yerel IP'nin dış dünyaya Public IP ile çıkması |
| **12** | **VLAN & Trunking** | `ip link add type vlan` | 802.1Q etiketli mantıksal sanal alt arayüz oluşturma |
| **13** | **VPN Tünelleme** | `wg show` / `ip route get` | Şifreli sanal tünel üzerinden güvenli yönlendirme |
| **14** | **Proxy & Yük Dengeleme** | `curl -x` / `curl -I localhost` | Forward vekil sunucu filtreleme & Reverse proxy karşılaması |
| **15** | **Bütünleşik Canlı Test** | Bash Otomasyon Scripti | Tüm zinciri tek seferde uçtan uca test etme |

---

## 01. MAC Adresini İnceleme ve Test Etme

Ağ kartınızın fiziksel donanım kimliğini görmek ve geçici olarak değiştirmek (*spoofing*) için:

```bash
# 1. Mevcut ağ kartlarını ve MAC adreslerini listele
ip link show

# Terminalinizdeki Gerçek Çıktı (Mirrored Ağ Modu):
# 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
#    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
# 2: eth0: <BROADCAST,MULTICAST> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
#    link/ether 00:15:5d:eb:99:b8 brd ff:ff:ff:ff:ff:ff
# 3: eth1: <BROADCAST,MULTICAST> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
#    link/ether 90:82:c3:3e:74:45 brd ff:ff:ff:ff:ff:ff
# 4: eth2: <BROADCAST,MULTICAST> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
#    link/ether 00:ff:36:f4:d5:44 brd ff:ff:ff:ff:ff:ff
# 5: loopback0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
#    link/ether 00:15:5d:7b:60:3f brd ff:ff:ff:ff:ff:ff
# 6: eth3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
#    link/ether 50:2e:91:64:40:5e brd ff:ff:ff:ff:ff:ff
#    altname enx502e9164405e
```

> 🔍 **Çıktının Detaylı Analizi (Tüm Arayüzlerin Görevleri):**
> * **`1: lo` (Standart Linux Loopback):**
>   * Linux çekirdeğinin kendi içindeki servislerle konuşmasını sağlayan klasik sanal döngüdür (`localhost` / `127.0.0.1`).
>   * Donanımsal bir kart olmadığı için MAC adresi boştur: `link/loopback 00:00:00:00:00:00`.
> * **`5: loopback0` (Windows $\leftrightarrow$ Linux Aynalama Köprüsü):**
>   * `networkingMode=mirrored` ile gelen özel sanal bağdaştırıcıdır.
>   * Microsoft sanal donanım kodu taşır (`link/ether 00:15:5d:7b:60:3f`).
>   * **Görevi:** Windows tarafındaki `localhost` ile Linux tarafındaki `localhost` portlarını birbirine bağlamaktır. Windows'ta veya Linux'ta açılan bir web sunucusuna her iki taraftan da erişilmesini sağlar.
> * **`2: eth0`, `3: eth1`, `4: eth2` (`state DOWN`):**
>   * Windows bilgisayarınızdaki kablo takılı olmayan Ethernet portları, Bluetooth ağ bağdaştırıcısı veya sanal VPN arayüzleridir. Aktif bağlantı olmadığı için durumları `DOWN` gözükür.
> * **`6: eth3` (`state UP` - Asıl Fiziksel Ağ Kartınız / NIC):**
>   * Bilgisayarınızı modeme ve internete bağlayan **ana aktif karttır**.
>   * `link/ether 50:2e:91:64:40:5e` $\rightarrow$ Bilgisayarınızın Wi-Fi veya Ethernet donanımının **gerçek fabrika çıkışlı 48-bit fiziksel MAC adresidir**!
>   * `brd ff:ff:ff:ff:ff:ff` $\rightarrow$ Katman 2 Ethernet genel yayın (*Broadcast*) adresidir.

```bash
# 2. Geçici MAC Adresi Değiştirme (MAC Spoofing Testi):
sudo ip link set dev eth3 down
sudo ip link set dev eth3 address 00:11:22:33:44:55
sudo ip link set dev eth3 up

# Tekrar doğrula:
ip link show eth3
```

---

## 02. DHCP DORA Sürecini ve Parametrelerini İnceleme

Cihazınızın ağa ilk katıldığında DHCP sunucusundan nasıl parametre aldığını görmek için:

```bash
# 1. NetworkManager kullanılıyorsa son DHCP olaylarını filtrele:
journalctl -u NetworkManager --grep="DHCP4" -n 25 --no-pager

# 2. Sistemdeki kayıtlı DHCP kira dosyasını (Option'lar dahil) incele:
cat /var/lib/NetworkManager/*.lease 2>/dev/null || cat /var/lib/dhcp/dhclient*.leases 2>/dev/null
```

> 🔍 **Örnek Çıktıda Neler Görünür?**
> - `fixed-address 192.168.1.50;` $\rightarrow$ Size atanan IP
> - `option subnet-mask 255.255.255.0;` $\rightarrow$ Alt ağ maskesi
> - `option routers 192.168.1.1;` $\rightarrow$ Option 3 (Default Gateway)
> - `option domain-name-servers 192.168.1.1, 8.8.8.8;` $\rightarrow$ Option 6 (DNS)
> - `lease time 86400;` $\rightarrow$ 24 saatlik kira süresi

---

## 03. IP Adresini (IPv4 & IPv6) Doğrulama

DHCP'den aldığınız mantıksal yönlendirilebilir Katman 3 adresini incelemek için:

```bash
# Hızlı ve özet görünüm:
ip -br addr show

# Detaylı IPv4 ve IPv6 adreslerini listele:
ip addr show eth0
```

```bash
# IPv6'yı anlık kapatıp sadece IPv4'e zorlama testi:
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
curl -4 https://icanhazip.com

# Tekrar Dual-Stack moduna alma:
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=0
```

---

## 04. Subnet Mask, CIDR ve Ağ Sınırlarını Hesaplama

Ağ kartınızın hangi mahallede (Subnet) yer aldığını görmek için:

```bash
# Alt ağ maskesini incele:
ip -4 addr show eth0 | grep inet

# Çıktı: inet 192.168.1.50/24 brd 192.168.1.255 scope global dynamic eth0
```

> 🧮 **Hesaplama:**
> - `/24` $\implies$ $255.255.255.0$
> - **Ağ Adı (Network ID):** `192.168.1.0` (İlk adres - cihaza verilemez)
> - **Kullanılabilir Cihaz IP Aralığı:** `192.168.1.1 - 192.168.1.254` (254 cihaz)
> - **Broadcast (Yayın) Adresi:** `192.168.1.255` (Son adres - cihaza verilemez)

Eğer sisteminizde `ipcalc` aracı yüklüyse (`sudo apt install ipcalc`):
```bash
ipcalc 192.168.1.50/24
```

---

## 05. Default Gateway (Varsayılan Ağ Geçidi) İnceleme

Yerel ağ dışındaki hedeflere (internete) çıkarken kullanılan rotayı kontrol etmek için:

```bash
# Yönlendirme tablosunu görüntüle:
ip route show

# Yalnızca varsayılan ağ geçidini filtrele:
ip route show default
# Çıktı: default via 192.168.1.1 dev eth0 proto dhcp metric 100
```

> ⚠️ **Gateway Olmazsa Ne Olur Testi?**
> ```bash
> # Geçici olarak varsayılan ağ geçidini silin:
> sudo ip route del default
> 
> # Yerel ağdaki cihaza ping atın (ÇALIŞIR):
> ping -c 2 192.168.1.1
> 
> # İnternete ping atın (HATA VERİR: Network is unreachable):
> ping -c 2 8.8.8.8
> 
> # Ağ geçidini geri ekleyin:
> sudo ip route add default via 192.168.1.1 dev eth0
> ```

---

## 06. ARP (Adres Çözümleme) Tablosunu İnceleme ve Test Etme

Modemin veya komşu makinelerin fiziksel MAC adreslerinin nasıl çözüldüğünü görmek için:

```bash
# Mevcut ARP önbelleğini görüntüle:
ip neigh show
# veya:
arp -n

# Çıktı: 192.168.1.1 dev eth0 lladdr 00:1a:2b:3c:4d:5e REACHABLE
```

```bash
# Gratuitous ARP (IP Çakışma Kontrolü Testi - arping ile):
# (Ağda 192.168.1.50 IP'sini kullanan başka biri var mı diye anons et)
sudo arping -D -I eth0 -c 2 192.168.1.50
# Çıkış kodu 0 ise IP boştadır; 1 dönerse çakışma vardır!
```

---

## 07. DNS (Alan Adı Çözümleme) Testleri

İnsanların okuduğu alan adlarının sayısal IP'ye nasıl çevrildiğini hiyerarşik olarak test etmek için:

```bash
# 1. Sistemde tanımlı DNS sunucularını gör:
cat /etc/resolv.conf
# veya modern systemd sistemlerde:
resolvectl status | grep "DNS Servers"

# 2. DNS A kaydını sorgula:
dig google.com +noall +answer

# 3. Kök sunuculardan başlayarak adım adım hiyerarşik çözümlemeyi izle (+trace):
dig google.com +trace
```

> 🔍 **Neyi Görürsünüz?** İstek önce Kök DNS sunucularına (`.` - Root Servers), oradan TLD sunucularına (`.com`), en son Google'ın yetkili sunucularına (`ns1.google.com`) gider ve IP'yi teslim alır.

---

## 08. Portlar ve Sockets (Açık Kapılar ve Oturumlar)

Sisteminizde hangi servislerin hangi portlarda beklediğini ve anlık soketleri görmek için:

```bash
# Dinlenen tüm TCP ve UDP portlarını numaraları ve süreç isimleriyle gör:
ss -tulpn

# Anlık kurulmuş aktif bağlantı soketlerini (IP:Port -> IP:Port) listele:
ss -tan state established
```

> 🔍 **Örnek Çıktı:**
> `ESTAB 0 0 192.168.1.50:52110 -> 142.250.184.206:443`
> İstemci soketi: `192.168.1.50:52110` (Geçici Ephemeral Port)  
> Hedef sunucu soketi: `142.250.184.206:443` (Google HTTPS)

---

## 09. TCP 3-Way Handshake Paketlerini Canlı Yakalama

Web bağlantısı kurulurken gerçekleşen `SYN -> SYN-ACK -> ACK` paketlerini terminalde canlı yakalamak için:

1. **Terminal 1'de Dinlemeyi Başlatın:**
```bash
sudo tcpdump -nn -i any "tcp[tcpflags] & (tcp-syn|tcp-ack) != 0 and host 1.1.1.1" -c 4
```

2. **Terminal 2'de Bağlantı İsteği Atın:**
```bash
curl -I https://1.1.1.1
```

3. **Terminal 1 Çıktısını İnceleyin:**
```text
1. 192.168.1.50.54321 > 1.1.1.1.443: Flags [S], seq 1000 ...        (SYN: Bağlanmak istiyorum)
2. 1.1.1.1.443 > 192.168.1.50.54321: Flags [S.], seq 2000, ack 1001 (SYN-ACK: Kabul, ben de hazırım)
3. 192.168.1.50.54321 > 1.1.1.1.443: Flags [.], ack 2001            (ACK: Anlaştık, başla)
```

---

## 10. Güvenlik Duvarı (Firewall / Stateful Inspection) İnceleme

Paketlerin durum denetimi tablosundan nasıl geçtiğini görmek için:

```bash
# 1. Mevcut iptables filtre kurallarını sayaçlarla incele:
sudo iptables -L -n -v --line-numbers

# 2. Stateful bağlantı tablosunu (conntrack) canlı listele:
sudo conntrack -L -p tcp --dport 443 2>/dev/null || cat /proc/net/nf_conntrack | grep 443
```

> 🔍 **Yorum:** Çıktıda `ESTABLISHED` durumunu görürsünüz. Bu, giden isteğin dönüş paketlerine güvenlik duvarının otomatik olarak izin verdiğini gösterir.

---

## 11. NAT (Ağ Adresi Çevirisi) İnceleme

Yerel ağ IP'nizin dış dünyaya Public IP ile çıkışını ve router kurallarını test etmek için:

```bash
# 1. Yerel IP'niz:
ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'

# 2. İnternette görünen genel Public IP'niz (NAT sonrası):
curl -s https://icanhazip.com

# 3. Eğer Linux makineniz bir router ise NAT (Masquerade) kurallarını listele:
sudo iptables -t nat -L -n -v
```

> 🔍 **Yorum:** İki IP birbirinden farklıdır. Modemin arkasındaki `192.168.1.50` yerel IP'niz, internet servis sağlayıcının verdiği `88.240.x.x` genel IP'sine çevrilmiştir (*PAT - Port Address Translation*).

---

## 12. VLAN (Virtual LAN) Alt Arayüzü Oluşturma ve Test Etme

Linux çekirdeğinde Katman 2 seviyesinde IEEE 802.1Q etiketli sanal alt ağ açmak için:

```bash
# 1. eth0 arayüzüne bağlı VLAN 10 alt arayüzü oluştur:
sudo ip link add link eth0 name eth0.10 type vlan id 10

# 2. Sanal VLAN arayüzüne IP ata ve ayağa kaldır:
sudo ip addr add 10.10.10.5/24 dev eth0.10
sudo ip link set dev eth0.10 up

# 3. VLAN etiketleme detayını doğrula:
ip -d link show eth0.10
# Çıktı: vlan protocol 802.1Q id 10 ...
```

---

## 13. VPN (Şifreli Tünel) İnceleme (WireGuard / IPsec)

Bir VPN tüneli üzerinden güvenli yönlendirilmeyi doğrulamak için:

```bash
# WireGuard tüneli varsa:
sudo wg show

# Belirli bir şirket içi IP'ye giderken hangi arayüzün (tünelin) seçildiğini test et:
ip route get 10.50.1.1
# Örnek Çıktı: 10.50.1.1 dev wg0 src 10.50.1.5 uid 1000 (Tünel devrededir!)
```

---

## 14. Proxy (Vekil Sunucu) ve Yük Dengeleme Testi

İstemci adına vekillik yapan Forward Proxy veya sunucu önündeki Nginx Reverse Proxy'yi test etmek için:

```bash
# 1. Forward Proxy üzerinden web isteği atma testi:
curl -x http://127.0.0.1:8080 -I https://google.com

# 2. Reverse Proxy (Nginx) arkasındaki sunucu başlıklarını inceleme:
curl -I http://localhost
```

> 🔍 **Neye Bakıyoruz?** Yanıt başlıklarında `Server: nginx`, `X-Forwarded-For` ve `X-Real-IP` başlıklarının yer alması, isteğin vekil sunucu tarafından karşılandığını doğrular.

---

## 15. 🚀 Bütünleşik Canlı Test Scripti (Tek Komutla 15 Adımı Raporlama)

Aşağıdaki hazır Bash scriptini Linux makinenizde çalıştırarak tüm bu ağ parametrelerini tek bir ekranda sıralı rapor olarak alabilirsiniz:

```bash
cat << 'EOF' > test_network_lifecycle.sh
#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "🌐 LİNUX AĞ YAŞAM DÖNGÜSÜ KONTROL RAPORU"
echo "=========================================================="

echo -e "\n[01. MAC Adresi]"
ip link show | grep -E "link/ether" | head -n 1

echo -e "\n[02. DHCP Durumu]"
journalctl -u NetworkManager --grep="DHCP" -n 2 --no-pager 2>/dev/null || echo "DHCP logları okunamadı veya statik yapılandırma."

echo -e "\n[03. IP Adresi (IPv4 / IPv6)]"
ip -br addr show | grep -v "127.0.0.1"

echo -e "\n[04. Subnet Mask & Broadcast]"
ip -4 addr show | grep -E "inet " | grep -v "127.0.0.1"

echo -e "\n[05. Default Gateway]"
ip route show default

echo -e "\n[06. ARP Tablosu (Gateway MAC)]"
ip neigh show | head -n 3

echo -e "\n[07. DNS Çözümleme (google.com)]"
dig google.com +short | head -n 2

echo -e "\n[08. Portlar ve Soketler (Dinlenen Servisler)]"
ss -tulpn | head -n 5

echo -e "\n[09. TCP Bağlantı Testi (Google HTTPS 443)]"
curl -I -s --connect-timeout 3 https://google.com | head -n 1

echo -e "\n[10. Güvenlik Duvarı Durumu]"
sudo iptables -S INPUT 2>/dev/null | head -n 3 || echo "iptables izinleri için sudo gereklidir."

echo -e "\n[11. NAT / Genel (Public) IP]"
curl -s --max-time 3 https://icanhazip.com || echo "Dış internet Public IP alınamadı."

echo -e "\n=========================================================="
echo "✅ Kontrol tamamlandı!"
EOF

chmod +x test_network_lifecycle.sh
./test_network_lifecycle.sh
```

---

> 🧪 **Docker ile İzolasyon Laboratuvarları:**  
> Bu adımları tek tek Docker konteynerleri üzerinde oluşturup yönlendiricileri ve güvenlik duvarlarını canlı denemek için [**`labs/` dizinine göz atabilirsiniz**](labs/README.md).
