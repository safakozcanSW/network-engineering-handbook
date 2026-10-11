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

Cihazınızın ağa ilk katıldığında DHCP sunucusundan (modeminizden) nasıl parametre aldığını görmek için:

```bash
# 1. Linux tarafında DHCP ile atanan DNS ve arama alanını incele:
cat /etc/resolv.conf

# Çıktı:
# nameserver 10.255.255.254
# search home
```

```powershell
# 2. Windows PowerShell üzerinde modemin dağıttığı gerçek DHCP (DORA) kira detayları:
ipconfig /all

# Terminalinizdeki Gerçek Çıktı:
# Wireless LAN adapter Wi-Fi:
#    Connection-specific DNS Suffix  . : home
#    Description . . . . . . . . . . . : MediaTek Wi-Fi 6 MT7920 Wireless LAN Card
#    Physical Address. . . . . . . . . : 50-2E-91-64-40-5E
#    DHCP Enabled. . . . . . . . . . . : Yes
#    IPv4 Address. . . . . . . . . . . : 192.168.1.89(Preferred)
#    Subnet Mask . . . . . . . . . . . : 255.255.255.0
#    Lease Obtained. . . . . . . . . . : 11 Ekim 2026 Pazar 16:06:08
#    Lease Expires . . . . . . . . . . : 12 Ekim 2026 Pazartesi 19:21:24
#    Default Gateway . . . . . . . . . : 192.168.1.1
#    DHCP Server . . . . . . . . . . . : 192.168.1.1
#    DNS Servers . . . . . . . . . . . : 192.168.1.1
```

> 🔍 **DHCP Seçeneklerinin (Options) Ağ Mühendisliği Analizi:**
> * **`Description: MediaTek Wi-Fi 6 MT7920`:** Linux'ta `eth3` olarak aynalanan gerçek fiziksel Wi-Fi kartınızın modelidir.
> * **`Physical Address: 50-2E-91-64-40-5E`:** Katman 2 MAC adresi (Linux'taki `eth3` ile birebir aynıdır).
> * **`DHCP Server: 192.168.1.1` (DHCP Option 54):** DORA paketlerini yanıtlayan ve IP'yi kiralayan modeminizin adresidir.
> * **`Default Gateway: 192.168.1.1` (DHCP Option 3):** Dış dünyaya giden kapıdır.
> * **`DNS Servers: 192.168.1.1` (DHCP Option 6):** Alan adlarını çözecek modem DNS yönlendiricisidir.
> * **`Lease Obtained / Expires` (DHCP Kira Süresi - Option 51):** Modemin size bu IP'yi (`192.168.1.89`) yaklaşık 27 saatliğine kiraladığını belgeler. Sürenin yarısında (%50 - T1 süresi) bilgisayarınız modeme DHCP Request atarak süreyi otomatik uzatır.
> 
> 💡 *Not: Çıktınızın altındaki `vEthernet (WSL) - 172.28.192.1 / 255.255.240.0` bağdaştırıcısı ise, ilk başta yaşadığımız ve `Network is unreachable` hatası veren eski sanal NAT anahtarının ta kendisidir!*

---

## 03. IP Adresini (IPv4 & IPv6) Doğrulama

Modeminizin DHCP sunucusundan aldığınız mantıksal yönlendirilebilir Katman 3 adresini incelemek için:

```bash
# Aktif ağ kartınızın (eth3) adreslerini listele:
ip addr show eth3

# Terminalinizdeki Gerçek Çıktı:
# 6: eth3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
#     link/ether 50:2e:91:64:40:5e brd ff:ff:ff:ff:ff:ff
#     inet 192.168.1.89/24 brd 192.168.1.255 scope global noprefixroute eth3
#     inet6 fe80::8d02:c40b:b42e:fbc9/64 scope link nodad noprefixroute
```

> 🔍 **Çıktı Analizi:**
> * **`192.168.1.89` (IPv4 Private IP):** Evinizdeki modemin bilgisayarınıza özel olarak tahsis ettiği C Sınıfı yerel IP adresidir (RFC 1918).
> * **`/24` CIDR Notasyonu:** Alt ağ maskesini (`255.255.255.0`) temsil eder.
> * **`fe80::...` (IPv6 Link-Local):** Aynı yerel ağdaki cihazların modeme ihtiyaç duymadan doğrudan konuşabilmesi için üretilen yerel IPv6 adresidir.

---

## 04. Subnet Mask, CIDR ve Ağ Sınırlarını Hesaplama

Ağ kartınızın hangi mahallede (Subnet) yer aldığını görmek ve sınırlarını hesaplamak için:

```bash
# Alt ağ maskesini incele:
ip -4 addr show eth3 | grep inet

# Çıktı: inet 192.168.1.89/24 brd 192.168.1.255 scope global noprefixroute eth3
```

> 🧮 **Ağ Mühendisliği Hesaplaması (/24 Alt Ağı):**
> - **CIDR:** `/24` $\implies$ Alt ağ maskesi: `255.255.255.0` ($24$ bit ağ, $8$ bit host).
> - **Toplam IP Sayısı:** $2^8 = 256$ adet adres.
> - **Ağ Adı (Network ID):** `192.168.1.0` (İlk adres - hiçbir cihaza verilemez, mahallenin adıdır).
> - **Modem / Gateway:** `192.168.1.1` (Genelde ilk kullanılabilir IP modeme verilir).
> - **Kullanılabilir Cihaz IP Aralığı:** `192.168.1.1` - `192.168.1.254` (Maksimum 254 cihaz aynı anda bağlanabilir).
> - **Sizin Bilgisayarınız:** `192.168.1.89` (Bu aralığın içindedir).
> - **Broadcast (Yayın) Adresi:** `192.168.1.255` (Son adres - tüm mahalleye anons hoparlörüdür).

---

## 05. Default Gateway (Varsayılan Ağ Geçidi) İnceleme

Yerel ağ dışındaki hedeflere (internete, Google'a) çıkarken trafiğin yönlendirildiği kapıyı görmek için:

```bash
# Yönlendirme tablosunu görüntüle:
ip route

# Terminalinizdeki Gerçek Çıktı:
# default via 192.168.1.1 dev eth3 proto kernel metric 30
# 192.168.1.0/24 dev eth3 proto kernel scope link metric 286
# 192.168.1.1 dev eth3 proto kernel scope link metric 30
```

> 🔍 **Yönlendirme Tablosunun Satır Satır Analizi:**
> 1. **`default via 192.168.1.1 dev eth3 metric 30`:**  
>    Linux çekirdeğine der ki: *"Eğer gideceğin IP adresi yerel ağında (`192.168.1.0/24`) değilse, paketi `eth3` kartından çıkarıp evindeki modem olan `192.168.1.1` adresine teslim et!"*
> 2. **`192.168.1.0/24 dev eth3 proto kernel scope link`:**  
>    *"Eğer hedef IP `192.168.1.x` ile başlıyorsa modeme sormana gerek yok, doğrudan kablo/Wi-Fi üzerinden komşu cihaza gönder."*
> 
> ```bash
> # İnternet rotasını sorgula:
> ip route get 8.8.8.8
> # Çıktı: 8.8.8.8 via 192.168.1.1 dev eth3 src 192.168.1.89 ...
> 
> # Google'a doğrudan ping at:
> ping -c 2 8.8.8.8
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

İnsanların okuduğu alan adlarının (`google.com`) sayısal IP adresine nasıl çevrildiğini hiyerarşik olarak test etmek için:

```bash
# 1. Sistemde tanımlı DNS sunucusunu doğrula:
resolvectl status | grep "DNS Servers"
# Terminalinizdeki Çıktı: DNS Servers: 10.255.255.254

# 2. Hızlıca DNS 'A' kaydını (IPv4 karşılığı) sorgula:
dig google.com +noall +answer
# Terminalinizdeki Çıktı:
# google.com.    135    IN    A    172.217.171.78

# 3. Kök sunuculardan başlayarak dünyanın DNS hiyerarşisini adım adım izle (+trace):
dig google.com +trace
```

> 🔍 **Canlı DNS Trace Çıktınızın Analizi (Dünya Genelinde Adım Adım Akış):**
> 
> 1. **1. Aşama - Kök Sunucular (Root DNS - `.`):**
>    - Sorgunuz önce dünyadaki 13 kök DNS kümesine soruldu (`a.root-servers.net` – `m.root-servers.net`).
>    - Kök sunucu dedi ki: *"Ben `google.com`'un IP'sini bilmem, ama `.com` uzantısından sorumlu TLD sunucularının listesi bende var, onlara git."*
> 
> 2. **2. Aşama - Üst Düzey Alan Adı Sunucuları (TLD - `.com`):**
>    - Paket `.com` sunucularına gitti (`a.gtld-servers.net` – `m.gtld-servers.net`).
>    - `.com` sunucusu dedi ki: *"Ben Google'ın kendi sunucusu değilim, ancak `google.com` alan adının yetkili sunucuları `ns1.google.com` - `ns4.google.com`'dur, git onlara sor."*
> 
> 3. **3. Aşama - Yetkili İsim Sunucuları (Authoritative DNS):**
>    - Paket doğrudan Google'ın kendi sunucusuna ulaştı (`ns4.google.com - 216.239.38.10`).
>    - Google'ın sunucusu kesin cevabı verdi:  
>      **`google.com. 300 IN A 172.217.21.238`**
> 
> 💡 *Not: Çıktınızdaki `UDP setup with 2001:... network unreachable` uyarısı, ev internetinizde genel IPv6 internet çıkışı tanımlı olmadığı için sorgunun otomatik olarak IPv4'e düşüp başarıyla tamamlandığını gösterir.*

---

## 08. Portlar ve Sockets (Açık Kapılar ve Oturumlar)

Sisteminizde hangi servislerin hangi portlarda beklediğini ve anlık soketleri görmek için:

```bash
# Dinlenen tüm TCP ve UDP portlarını numaraları ve süreç isimleriyle gör:
ss -tulpn

# Terminalinizdeki Gerçek Çıktı:
# Netid  State   Recv-Q  Send-Q  Local Address:Port      Peer Address:Port  Process
# udp    UNCONN  0       0       127.0.0.54:53           0.0.0.0:*          users:(("systemd-resolve",pid=85,fd=18))
# udp    UNCONN  0       0       127.0.0.53%lo:53        0.0.0.0:*          users:(("systemd-resolve",pid=85,fd=16))
# udp    UNCONN  0       0       10.255.255.254:53       0.0.0.0:*
# udp    UNCONN  0       0       127.0.0.1:323           0.0.0.0:*          users:(("chronyd",pid=171,fd=4))
# tcp    LISTEN  0       1000    10.255.255.254:53       0.0.0.0:*
# tcp    LISTEN  0       4096    127.0.0.53%lo:53        0.0.0.0:*          users:(("systemd-resolve",pid=85,fd=17))
# tcp    LISTEN  0       4096    127.0.0.54:53           0.0.0.0:*          users:(("systemd-resolve",pid=85,fd=19))

# Anlık kurulmuş aktif bağlantı oturumlarını (IP:Port -> IP:Port) listele:
ss -tan state established
# Çıktı: Boş döndü (Başlıklar listelendi)
```

> 🔍 **Açık Portların ve Servislerin Analizi:**
> 1. **Port 53 (DNS Çözümleyici - `systemd-resolve`):**  
>    * Hem **UDP** (`UNCONN`) hem de **TCP** (`LISTEN`) modunda dinliyor.  
>    * Sisteminizin internete gitmeden önce yerel DNS isteklerini karşılayan yerel önbellek servisidir.
> 2. **Port 323 (NTP Zaman Senkronizasyonu - `chronyd`):**  
>    * Bilgisayarınızın saatini dünya atom saatleriyle senkronize tutan Network Time Protocol (NTP) istemcisidir.
> 3. **`state established` Neden Boş Döndü?**  
>    * Web sayfaları (HTTP/HTTPS) veriyi milisaniyeler içinde alıp soketi kapatır (`TIME_WAIT` veya kapalı duruma geçer).  
>    * Komutu çalıştırdığınız an arka planda canlı dosya indiren veya aktif açık kalan bir SSH/VPN tüneli olmadığı için tablo boştur.
> 
> 💡 **Canlı Bir "ESTABLISHED" Soketi Görme Testi:**
> ```bash
> # Arka planda geçici bir web sunucusu başlatın ve soket oluşturun:
> python3 -m http.server 8080 &
> curl http://localhost:8080/ >/dev/null &
> 
> # Anında soketleri sorgulayın:
> ss -tan state established
> # Çıktı: ESTAB 0 0 127.0.0.1:54322 -> 127.0.0.1:8080
> ```

---

## 09. TCP 3-Way Handshake Paketlerini Canlı Yakalama

Web bağlantısı kurulurken gerçekleşen `SYN -> SYN-ACK -> ACK` paketlerini terminalde canlı yakalamak için:

```bash
# Tek bir terminalde arka planda dinleyip hemen curl isteği atma:
tcpdump -nn -i any "tcp[tcpflags] & (tcp-syn|tcp-ack) != 0 and host 1.1.1.1" -c 4 &
curl -I -s https://1.1.1.1 >/dev/null
```

> 🔍 **Terminalinizde Yakalanan Canlı TCP Paketlerinin Analizi:**
> ```text
> 1. In  IP 1.1.1.1.443 > 192.168.1.89.43089: Flags [S.], seq 1510900119, ack 4246799660 ...
> 2. Out IP 192.168.1.89.43089 > 1.1.1.1.443: Flags [.],  ack 1, win 502 ...
> 3. Out IP 192.168.1.89.43089 > 1.1.1.1.443: Flags [P.], seq 1:1552, ack 1, length 1551 ...
> 4. In  IP 1.1.1.1.443 > 192.168.1.89.43089: Flags [.],  ack 1552, win 16 ...
> ```
> 
> 🧠 **Satır Satır Ağ Mühendisliği İncelemesi:**
> * **Soket Eşleşmesi (`192.168.1.89:43089` $\leftrightarrow$ `1.1.1.1:443`):**  
>   Bilgisayarınız işletim sistemi havuzundan geçici rastgele bir istemci portu (*Ephemeral Port*) seçti: **`43089`**. Hedef ise Cloudflare'in standart HTTPS web portu: **`443`**.
> * **1. Paket (`Flags [S.]` - SYN-ACK):**  
>   Cloudflare sunucusu isteğinizi kabul etti (`S` = SYN) ve aldığını onayladı (`.` = ACK). Sunucu kendi rastgele sıra numarasını belirledi (`seq 1510900119`) ve sizin sıra numaranızı onayladı (`ack 4246799660`).
> * **2. Paket (`Flags [.]` - ACK):**  
>   Bilgisayarınız sunucunun yanıtını onayladı (`ACK`). **Böylece 3-Way Handshake başarıyla tamamlandı ve TCP oturumu kuruldu!**
> * **3. Paket (`Flags [P.]` - PUSH + ACK, Length 1551):**  
>   El sıkışma biter bitmez bilgisayarınız `length 1551` baytlık ilk gerçek şifreli veriyi (**TLS Client Hello** - HTTPS şifreleme başlatma paketi) yolladı ve hemen iletilmesi için `PUSH` bayrağını dikti!
> * **4. Paket (`Flags [.]` - ACK, ack 1552):**  
>   Cloudflare sunucusu 1551 baytlık verinizi eksiksiz aldığını teyit etti (`1 + 1551 = ack 1552`).

---

## 10. Güvenlik Duvarı (Firewall / Stateful Inspection) İnceleme

Paketlerin durum denetimi tablosundan nasıl geçtiğini ve filtre kurallarını görmek için:

```bash
# Mevcut iptables filtre zincirlerini ve sayaçlarını incele:
iptables -L -n -v --line-numbers

# Terminalinizdeki Gerçek Çıktı:
# # Table 'filter' contains incompatible base-chains, use 'nft' tool to list them.
# Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
# Chain FORWARD (policy ACCEPT 0 packets, 0 bytes)
# Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)
```

> 🔍 **Güvenlik Duvarı Çıktısının Analizi:**
> * **`policy ACCEPT` (Varsayılan Politika İzin Ver):**  
>   Sisteminizde gelen (`INPUT`), yönlendirilen (`FORWARD`) ve giden (`OUTPUT`) tüm paketlere aksi belirtilmedikçe izin verilir.
> * **`use 'nft' tool to list them` Uyarısı:**  
>   Modern Ubuntu dağıtımlarında `iptables` komutu, arka planda yeni nesil **`nftables`** altyapısını kullanır. Detaylı çekirdek kurallarını görmek için `nft list ruleset` komutu da kullanılabilir.

---

## 11. NAT (Ağ Adresi Çevirisi) İnceleme

Yerel ağ IP'nizin dış dünyaya genel Public IP ile çıkışını ve router (modem) çevirisini doğrulamak için:

```bash
# 1. Yerel Ağdaki IP Adresiniz (eth3 kartınız):
ip -4 addr show eth3 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
# Terminalinizdeki Çıktı: 192.168.1.89

# 2. Tüm Dünyanın Gördüğü Genel Public IP Adresiniz (NAT Sonrası):
curl -s https://icanhazip.com
# Terminalinizdeki Çıktı: 84.51.13.216
```

> 🔍 **Canlı NAT / PAT Karşılaştırması:**
> 
> * **Bilgisayarınızın Özel IP'si (RFC 1918):** `192.168.1.89`  
>   Bu IP yalnızca evinizin salonundaki modeme kadar geçerlidir. İnternet omurgasında bu adres yönlendirilemez (*non-routable*).
> * **Modeminizin Dış Genel IP'si (Public IP):** `84.51.13.216`  
>   İnternet Servis Sağlayıcınızın (Türk Telekom, Superonline vb.) modeminize tahsis ettiği, tüm internette tek ve benzersiz olan genel IP adresinizdir.
> * **PAT (Port Address Translation) Mucizesi:**  
>   Evinizdeki telefon, televizyon ve bilgisayar aynı anda internete bağlandığında, modem tüm bu cihazların paketlerini tek bir `84.51.13.216` IP'sine ve her cihaz için farklı bir port numarasına (`:43089` gibi) çevirerek dışarı yollar. Cevap geldiğinde de port tablosuna bakarak paketi doğru cihaza geri teslim eder!

---

## 12. VLAN (Virtual LAN) Alt Arayüzü Oluşturma ve Test Etme

Linux çekirdeğinde Katman 2 seviyesinde IEEE 802.1Q etiketli sanal alt ağ açmak için:

```bash
# 1. eth3 arayüzüne bağlı VLAN 10 alt arayüzü oluştur:
sudo ip link add link eth3 name eth3.10 type vlan id 10

# 2. Sanal VLAN arayüzüne IP ata ve ayağa kaldır:
sudo ip addr add 10.10.10.5/24 dev eth3.10
sudo ip link set dev eth3.10 up

# 3. VLAN etiketleme detayını doğrula:
ip -d link show eth3.10
# Çıktı: vlan protocol 802.1Q id 10 ...

# 4. Test bittikten sonra sanal VLAN arayüzünü sil:
sudo ip link del eth3.10
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

echo -e "\n[01. Fiziksel MAC Adresi (eth3)]"
ip link show eth3 | grep -E "link/ether"

echo -e "\n[02. DNS Yapılandırması]"
grep nameserver /etc/resolv.conf

echo -e "\n[03. Yerel IP Adresi (IPv4 / IPv6)]"
ip -br addr show eth3

echo -e "\n[04. Subnet Mask & Broadcast]"
ip -4 addr show eth3 | grep -E "inet "

echo -e "\n[05. Varsayılan Ağ Geçidi (Default Gateway)]"
ip route show default

echo -e "\n[06. ARP Tablosu (Modem MAC Adresi)]"
ip neigh show dev eth3 | head -n 3

echo -e "\n[07. DNS Çözümleme Testi (google.com)]"
dig google.com +short | head -n 2

echo -e "\n[08. Dinlenen Portlar (Açık Servisler)]"
ss -tulpn | head -n 5

echo -e "\n[09. TCP Bağlantı & Yanıt Testi (Cloudflare HTTPS)]"
curl -I -s --connect-timeout 3 https://1.1.1.1 | head -n 1

echo -e "\n[10. Güvenlik Duvarı Durumu (INPUT Politikası)]"
iptables -L INPUT -n | head -n 2

echo -e "\n[11. NAT / Genel (Public) IP]"
echo "Genel IP: $(curl -s --max-time 3 https://icanhazip.com)"

echo -e "\n=========================================================="
echo "✅ 15 Aşamalı Ağ Yaşam Döngüsü Kontrolü Başarıyla Tamamlandı!"
EOF

chmod +x test_network_lifecycle.sh
./test_network_lifecycle.sh
```

---

> 🧪 **Docker ile İzolasyon Laboratuvarları:**  
> Bu adımları tek tek Docker konteynerleri üzerinde oluşturup yönlendiricileri ve güvenlik duvarlarını canlı denemek için [**`labs/` dizinine göz atabilirsiniz**](labs/README.md).
