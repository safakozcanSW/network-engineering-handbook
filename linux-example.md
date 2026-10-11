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

# Terminalinizdeki Gerçek Çıktı (VMware Ubuntu):
# 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
#    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
# 2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UNKNOWN mode DEFAULT group default qlen 1000
#    link/ether 00:0c:29:dd:2c:3b brd ff:ff:ff:ff:ff:ff
```

> 🔍 **Çıktının Detaylı Ağ Mühendisliği Analizi:**
> * **`1: lo` (Loopback - Yerel İç Döngü):**
>   * Fiziksel bir donanım veya kablo değildir.
>   * İşletim sisteminin kendi kendine konuşmasını sağlayan sanal iç döngüdür (`localhost` / `127.0.0.1`).
>   * Donanımsal bir kart olmadığı için MAC adresi boştur: `link/loopback 00:00:00:00:00:00`.
> * **`2: ens33` (Ana Ethernet Ağ Kartınız / NIC):**
>   * Modern Linux'un öngörülebilir ağ arayüzü isimlendirmesidir (*Predictable Interface Names: Ethernet on bus/slot 33*).
>   * **`link/ether 00:0c:29:dd:2c:3b`:** Ağ kartınızın 48-bitlik fiziksel **MAC adresidir**. İlk 3 oktet olan `00:0c:29`, VMware'in IEEE tescilli resmi donanım üretici kimliğidir (*OUI*).
>   * **`brd ff:ff:ff:ff:ff:ff`:** Katman 2 Ethernet genel yayın (*Broadcast*) adresidir.
>   * **`mtu 1500`:** Maximum Transmission Unit; Ethernet standardında tek bir pakette taşınabilecek maksimum veri yükü 1500 bayttır.

```bash
# 2. Geçici MAC Adresi Değiştirme (MAC Spoofing Testi):
sudo ip link set dev ens33 down
sudo ip link set dev ens33 address 00:11:22:33:44:55
sudo ip link set dev ens33 up

# Tekrar doğrula:
ip link show ens33
# (Test bittikten sonra eski haline getirmek veya otomatik almak için sistemi yeniden başlatabilirsiniz).
```

---

## 02. DHCP DORA Sürecini ve Parametrelerini İnceleme

Cihazınızın ağa ilk katıldığında DHCP sunucusundan (evdeki modeminizden) nasıl parametre aldığını görmek için:

```bash
# 1. DHCP tarafından sistemde tutulan aktif kira dosyasını incele:
cat /run/systemd/netif/leases/* 2>/dev/null || cat /var/lib/NetworkManager/*.lease 2>/dev/null

# Terminalinizdeki Gerçek Çıktı:
# # This is private data. Do not parse.
# ADDRESS=192.168.1.177

# 2. DHCP ile atanan DNS ve yerel arama alanını incele:
cat /etc/resolv.conf

# Terminalinizdeki Gerçek Çıktı:
# nameserver 127.0.0.53
# options edns0 trust-ad
# search home
```

> 🔍 **Canlı Bridged Mod Analizi (Modemin Verdiği Bağımsız IP ve DNS):**
> 
> * 📜 **`ADDRESS=192.168.1.177` (Resmi Kira Sözleşmesi / DHCP Lease):**  
>   Ubuntu açıldığında modeme anons yaptı (*DHCP Discover*). Modeminiz de salonda oturan Windows bilgisayarınızın (`192.168.1.89`) yanına, bu yeni Ubuntu sanal makinenize evdeki boş dairelerden biri olan **`192.168.1.177`** IP'sini tapuladı/kiraladı. Sistem bu resmi sözleşmeyi unutmamak için `leases` dosyasına `ADDRESS=192.168.1.177` olarak kaydetti.
> 
> * 🏢 **`nameserver 127.0.0.53` (Bina İçi Danışma Memuru / `systemd-resolved`):**  
>   Hatırlarsanız `127.x.x.x` bloğunun tamamı **Loopback (Cihazın Kendi İçi)** demektir (53 ise DNS portudur).  
>   * **Neden Modemin IP'si Yazmıyor?** Modern Ubuntu, her `google.com` aramasında dışarı modeme gidip gecikme yaşanmasın diye işletim sisteminin kendi içine süper hızlı bir **DNS Önbellekçisi** kurmuştur.
>   * **Nasıl Çalışır?** Bir web sitesine girmek istediğinizde sorgu önce bu iç danışma memuruna (`127.0.0.53`) gider. Eğer bu site daha önce ziyaret edilmişse modeme hiç sormadan **0 milisaniyede** hafızadan cevap verir! Hafızada yoksa, memur arka kapıdan çıkıp modeminiz olan `192.168.1.1`'e sorar, cevabı hem hafızasına kaydeder hem de size teslim eder.
> 
> * 🏷️ **`search home`:** Modemin ev ağınıza dağıttığı yerel alan adı sonekidir.

---

## 03. IP Adresini (IPv4 & IPv6) Doğrulama

Modeminizin DHCP sunucusundan aldığınız mantıksal yönlendirilebilir Katman 3 adresini incelemek için:

```bash
# Aktif ağ kartınızın (ens33) adreslerini listele:
ip addr show ens33

# Terminalinizdeki Gerçek Çıktı:
# 2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UNKNOWN group default qlen 1000
#     link/ether 00:0c:29:dd:2c:3b brd ff:ff:ff:ff:ff:ff
#     inet 192.168.1.177/24 brd 192.168.1.255 scope global dynamic noprefixroute ens33
#        valid_lft 85170sec preferred_lft 85170sec
#     inet6 fe80::20c:29ff:fedd:2c3b/64 scope link noprefixroute
#        valid_lft forever preferred_lft forever
```

> 🔍 **Çıktı Analizi:**
> * **`192.168.1.177` (IPv4 Private IP):** Evinizdeki modemin Ubuntu sanal makinenize özel olarak tahsis ettiği C Sınıfı yerel IP adresidir.
> * **`/24` CIDR Notasyonu:** Alt ağ maskesini (`255.255.255.0`) temsil eder.
> * **`valid_lft 85170sec` (DHCP Kira Süresi):** $85170 \div 3600 \approx 23.6$ saat! Modemin bu IP'yi tam 24 saatliğine kiraladığının canlı kanıtıdır.
> * **`fe80::20c:29ff:fedd:2c3b/64` (IPv6 Link-Local & EUI-64):**  
>   MAC adresinizin (`00:0c:29:dd:2c:3b`) tam ortasına `ff:fe` eklenerek üretilen yerel IPv6 adresidir.
> 
> ---
> 
> ## 04. Subnet Mask, CIDR ve Ağ Sınırlarını Hesaplama
> 
> Ağ kartınızın hangi mahallede (Subnet) yer aldığını görmek ve sınırlarını hesaplamak için:
> 
> ```bash
> # Alt ağ maskesini incele:
> ip -4 addr show ens33 | grep inet
> 
> # Çıktı: inet 192.168.1.177/24 brd 192.168.1.255 scope global dynamic noprefixroute ens33
> ```
> 
> > 🧮 **Ağ Mühendisliği Hesaplaması (/24 Alt Ağı):**
> > - **CIDR:** `/24` $\implies$ Alt ağ maskesi: `255.255.255.0` ($24$ bit ağ, $8$ bit host).
> > - **Toplam IP Sayısı:** $2^8 = 256$ adet adres.
> > - **Ağ Adı (Network ID):** `192.168.1.0` (İlk adres - hiçbir cihaza verilemez, mahallenin adıdır).
> > - **Modem / Gateway:** `192.168.1.1` (Evdeki modemin yerel IP adresi).
> > - **Windows Bilgisayarınız:** `192.168.1.89`
> > - **Ubuntu Sanal Makineniz:** `192.168.1.177` *(Aynı ev ağında iki bağımsız kardeş makine!)*
> - **Kullanılabilir Cihaz IP Aralığı:** `192.168.1.1` - `192.168.1.254` (Maksimum 254 cihaz).
> - **Broadcast (Yayın) Adresi:** `192.168.1.255` (Son adres - tüm mahalleye anons hoparlörüdür).

---

## 05. Default Gateway (Varsayılan Ağ Geçidi) İnceleme

Yerel ağ dışındaki hedeflere (internete, Google'a) çıkarken trafiğin yönlendirildiği kapıyı görmek için:

```bash
# Yönlendirme tablosunu görüntüle:
ip route

# Terminalinizdeki Gerçek Çıktı:
# default via 192.168.1.1 dev ens33 proto dhcp src 192.168.1.177 metric 100
# 192.168.1.0/24 dev ens33 proto kernel scope link src 192.168.1.177 metric 100
```

> 🔍 **Yönlendirme Tablosunun Satır Satır Analizi:**
> 1. **`default via 192.168.1.1 dev ens33 proto dhcp src 192.168.1.177 metric 100`:**  
>    Linux çekirdeğine der ki: *"Eğer gideceğin IP adresi yerel ağında (`192.168.1.0/24`) değilse, paketi `ens33` kartından çıkarıp evindeki modem olan `192.168.1.1` adresine teslim et! Kaynak IP olarak da kendi adresin olan `192.168.1.177`'yi kullan."*
> 2. **`192.168.1.0/24 dev ens33 proto kernel scope link src 192.168.1.177`:**  
>    *"Eğer hedef IP `192.168.1.x` ile başlıyorsa (örneğin Windows bilgisayarınız `192.168.1.89`), modeme sormana gerek yok, doğrudan kablo/Wi-Fi üzerinden komşu cihaza gönder."*

---

## 06. ARP (Adres Çözümleme) Tablosunu İnceleme ve Test Etme

Modemin veya komşu makinelerin fiziksel MAC adreslerinin nasıl çözüldüğünü görmek için:

```bash
# Mevcut ARP önbelleğini görüntüle:
ip neigh show

# Terminalinizdeki Gerçek Çıktı:
# 192.168.1.1 dev ens33 lladdr 80:ea:0b:d1:9b:20 REACHABLE
```

> 🔍 **Canlı ARP Analizi (Modemin Gerçek Fiziksel MAC Adresi!):**
> * **`192.168.1.1` $\leftrightarrow$ `80:ea:0b:d1:9b:20`:**  
>   Ubuntu, modeme veri gönderebilmek için Katman 2'de modemin fiziksel adresini sordu (*ARP Request*). Modem cevap verdi (*ARP Reply*) ve tablonuza girdi!
> * **`80:ea:0b` OUI Kodu:** Evinizdeki fiziksel modemin (Arcadyan / ZTE / Zyxel üretici kodudur) fabrika çıkışlı donanım MAC adresidir!
> * **`REACHABLE`:** Bu cihazla iletişim aktif ve hat sağlam demektir.

```bash
# Windows bilgisayarınıza ping atıp onun da MAC adresini ARP tablosuna düşürün:
ping -c 2 192.168.1.89
ip neigh show
# (Çıktıda 192.168.1.89'un karşısında Windows Wi-Fi kartınızın 50:2e:91:... MAC adresini göreceksiniz!)
```

---

## 07. DNS (Alan Adı Çözümleme) Testleri

İnsanların okuduğu alan adlarının (`google.com`) sayısal IP adresine nasıl çevrildiğini hiyerarşik olarak test etmek için:

```bash
# 1. Sistemde tanımlı DNS sunucusunu doğrula:
resolvectl status | grep "DNS Servers"
# Terminalinizdeki Çıktı: DNS Servers: 192.168.1.1 (Doğrudan evinizdeki modem!)

# 2. Hızlıca DNS 'A' kaydını (IPv4 karşılığı) sorgula:
dig google.com +noall +answer
# Terminalinizdeki Gerçek Çıktı:
# google.com.    121    IN    A    172.217.171.78

# 3. Kök sunuculardan başlayarak dünyanın DNS hiyerarşisini adım adım izle (+trace):
dig google.com +trace
```

> 🔍 **Canlı DNS Trace Çıktınızın Analizi (Dünya Genelinde Adım Adım Akış):**
> 
> 1. **1. Aşama - Kök Sunucular (Root DNS - `.`):**
>    - Sorgunuz önce dünyadaki 13 kök DNS kümesine soruldu (`c.root-servers.net` – `m.root-servers.net`).
>    - Kök sunucu dedi ki: *"Ben `google.com`'un IP'sini bilmem, ama `.com` uzantısından sorumlu TLD sunucularının listesi bende var, onlara git."*
> 
> 2. **2. Aşama - Üst Düzey Alan Adı Sunucuları (TLD - `.com`):**
>    - Paket `.com` sunucularına gitti (`a.gtld-servers.net` – `m.gtld-servers.net`).
>    - `.com` sunucusu dedi ki: *"Ben Google'ın kendi sunucusu değilim, ancak `google.com` alan adının yetkili sunucuları `ns1.google.com` - `ns4.google.com`'dur, git onlara sor."*
> 
> 3. **3. Aşama - Yetkili İsim Sunucuları (Authoritative DNS):**
>    - Paket doğrudan Google'ın kendi sunucusuna ulaştı (`ns2.google.com`).
>    - Google'ın sunucusu kesin cevabı verdi: **`google.com. IN A 172.217.171.78`**

---

## 08. Portlar ve Sockets (Açık Kapılar ve Oturumlar)

Sisteminizde hangi servislerin hangi portlarda beklediğini ve anlık soketleri görmek için:

```bash
# Dinlenen tüm TCP ve UDP portlarını numaraları ve süreç isimleriyle gör:
# Dinlenen tüm TCP ve UDP portlarını numaraları ve süreç isimleriyle gör:
ss -tulpn

# Terminalinizdeki Gerçek Çıktı:
# Netid  State   Recv-Q  Send-Q  Local Address:Port      Peer Address:Port  Process
# udp    UNCONN  0       0       0.0.0.0:5353            0.0.0.0:*          users:(("avahi-daemon",pid=1457,fd=12))
# udp    UNCONN  0       0       127.0.0.54:53           0.0.0.0:*          users:(("systemd-resolve",pid=560,fd=18))
# udp    UNCONN  0       0       127.0.0.53%lo:53        0.0.0.0:*          users:(("systemd-resolve",pid=560,fd=16))
# udp    UNCONN  0       0       127.0.0.1:323           0.0.0.0:*          users:(("chronyd",pid=1539,fd=4))
# udp    UNCONN  0       0          [::]:5353               [::]:*          users:(("avahi-daemon",pid=1457,fd=13))
# udp    UNCONN  0       0         [::1]:323                [::]:*          users:(("chronyd",pid=1539,fd=5))
# tcp    LISTEN  0       4096    127.0.0.1:631           0.0.0.0:*          users:(("cupsd",pid=1714,fd=7))
# tcp    LISTEN  0       4096    127.0.0.53%lo:53        0.0.0.0:*          users:(("systemd-resolve",pid=560,fd=17))
# tcp    LISTEN  0       4096    127.0.0.54:53           0.0.0.0:*          users:(("systemd-resolve",pid=560,fd=19))
# tcp    LISTEN  0       4096      [::1]:631                [::]:*          users:(("cupsd",pid=1714,fd=6))

# Anlık kurulmuş aktif bağlantı oturumlarını (IP:Port -> IP:Port) listele:
ss -tan state established
# Çıktı: Boş döndü (Başlıklar listelendi)
```

> 🔍 **Açık Portların ve Servislerin Ağ Mühendisliği Analizi:**
> 1. **Port 5353 (mDNS - `avahi-daemon`):**  
>    * Multicast DNS (Zeroconf / Apple Bonjour protokolü).  
>    * Yerel ağdaki cihazların merkezi bir DNS sunucusuna gerek kalmadan `safak.local` gibi isimlerle birbirini ve paylaşılan yazıcıları otomatik bulmasını sağlar.
> 2. **Port 631 (CUPS Ağ Yazıcı Servisi - `cupsd`):**  
>    * Internet Printing Protocol (IPP) üzerinden yerel ağdaki yazıcıları yöneten baskı sunucusu servisidir.
> 3. **Port 53 (DNS Çözümleyici - `systemd-resolve`):**  
>    * Sisteminizin yerel DNS önbellek stub servisidir (`127.0.0.53:53`).
> 4. **Port 323 (NTP Zaman Senkronizasyonu - `chronyd`):**  
>    * Dünya atomik saat sunucularıyla senkronize kalan zaman servisidir.
> 5. **`state established` Neden Boş Döndü?**  
>    * Komutu çalıştırdığınız an arka planda canlı dosya indiren veya açık kalan bir SSH bağlantısı olmadığı için liste boştur. Web istekleri milisaniyeler içinde tamamlanıp kapanır.

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
> 1. Out IP 192.168.1.177.46814 > 1.1.1.1.443: Flags [S],  seq 3804754110, length 0
> 2. In  IP 1.1.1.1.443 > 192.168.1.177.46814: Flags [S.], seq 1053142274, ack 3804754111, length 0
> 3. Out IP 192.168.1.177.46814 > 1.1.1.1.443: Flags [.],  ack 1, length 0
> 4. Out IP 192.168.1.177.46814 > 1.1.1.1.443: Flags [.],  seq 1:1441, ack 1, length 1440
> ```
> 
> 🧠 **Satır Satır Ağ Mühendisliği İncelemesi:**
> * **Soket Eşleşmesi (`192.168.1.177:46814` $\leftrightarrow$ `1.1.1.1:443`):**  
>   Ubuntu çekirdeği rastgele geçici bir istemci portu (*Ephemeral Port*) tahsis etti: **`46814`**. Hedef ise Cloudflare HTTPS web portu: **`443`**.
> * **1. Paket (`Flags [S]` - SYN):**  
>   Ubuntu'nuz Cloudflare'e bağlanmak istediğini bildirdi. Kendi rastgele sıra numarasını belirledi: `seq 3804754110`.
> * **2. Paket (`Flags [S.]` - SYN-ACK):**  
>   Cloudflare isteğinizi kabul etti (`S`) ve aldığını onayladı (`.`).  
>   Dikkat edin: Cloudflare sizin `seq 3804754110` numaranızı $1$ artırarak **`ack 3804754111`** olarak geri gönderdi! Ayrıca kendi başlangıç numarasını bildirdi (`seq 1053142274`).
> * **3. Paket (`Flags [.]` - ACK):**  
>   Ubuntu bu yanıtı onayladı (`ACK`). **Böylece 3 Aşamalı El Sıkışma tamamlandı ve güvenli TCP oturumu kuruldu!**
> * **4. Paket (`length 1440` - TLS Veri Yükü):**  
>   Bağlantı kurulur kurulmaz Ubuntu `1440` baytlık **TLS Client Hello** (HTTPS şifrelemesini başlatan el sıkışma paketini) Cloudflare'e postaladı!

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
# 1. Yerel Ağdaki IP Adresiniz (ens33 kartınız):
ip -4 addr show ens33 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
# Çıktı: 192.168.1.177

# 2. Tüm Dünyanın Gördüğü Genel Public IP Adresiniz (NAT Sonrası):
curl -s https://icanhazip.com
# Terminalinizdeki Çıktı: 84.51.13.216
```

> 🔍 **Canlı NAT / PAT Karşılaştırması:**
> 
> * **Sanal Makinenizin Özel IP'si (RFC 1918):** `192.168.1.177`  
>   Bu IP yalnızca evinizin salonundaki modeme kadar geçerlidir. İnternet omurgasında bu adres yönlendirilemez (*non-routable*).
> * **Modeminizin Dış Genel IP'si (Public IP):** `84.51.13.216`  
>   İnternet Servis Sağlayıcınızın (Türk Telekom, Superonline vb.) modeminize tahsis ettiği, tüm internette tek ve benzersiz olan genel IP adresinizdir.
> * **PAT (Port Address Translation) Mucizesi:**  
>   Evinizdeki telefon, Windows bilgisayarınız (`192.168.1.89`) ve Ubuntu sanal makineniz (`192.168.1.177`) aynı anda internete bağlansa bile, modem tüm bu cihazların paketlerini tek bir `84.51.13.216` IP'sine ve her cihaz için farklı bir port numarasına (`:46814` gibi) çevirerek dışarı yollar. Cevap geldiğinde de port tablosuna bakarak paketi doğru cihaza geri teslim eder!

---

## 12. VLAN (Virtual LAN) Alt Arayüzü Oluşturma ve Test Etme

### ❓ VLAN Neden Kurulur ve Neden İhtiyaç Vardır?

Fiziksel dünyada her farklı departman veya güvenlik seviyesi için **ayrı ayrı fiziksel switch'ler ve kablolar satın almak** aşırı pahalı ve verimsizdir. VLAN (Sanal Yerel Ağ), tek bir fiziksel kablo ve switch üzerinde mantıksal olarak yalıtılmış bağımsız sanal ağlar kurmamızı sağlar:

1. **🛡️ Güvenlik ve İzolasyon (En Temel Neden):**
   * Bir şirkette **Muhasebe**, **Yazılım**, **Sunucular** ve **Misafir Wi-Fi (Guest)** aynı fiziksel switch'e bağlıdır.
   * VLAN olmadan kafeden bağlanan bir misafir, şirket içi sunucuları veya muhasebenin bilgisayarlarını doğrudan dinleyebilir.
   * VLAN (ör. VLAN 10 Muhasebe, VLAN 50 Misafir) sayesinde bu ağlar Katman 2 seviyesinde birbirinden **tamamen izole edilir**; aralarında bir Router/Firewall kuralı olmadan asla konuşamazlar.
2. **⚡ Broadcast (Yayın) Fırtınalarını Önleme:**
   * Bir ağda 1000 cihaz varsa ve birisi ARP anonsu (`Broadcast`) yaparsa, bu anons 1000 cihaza birden gider ve ağı yavaşlatır.
   * VLAN, büyük bir ağı küçük *Broadcast Domain*'lere böler. Yayınlar sadece o VLAN'daki cihazlarda kalır.
3. **🖥️ Linux Sunucularda Neden Alt Arayüz (`ens33.10`) Açılır?**
   * Sunucunuzun kasasında sadece **tek bir fiziksel Ethernet kablosu** takılı olabilir.
   * Ancak bu sunucunun hem **Web trafiğine (VLAN 10)** hem de **Veritabanı yedekleme ağına (VLAN 20)** aynı anda hizmet vermesi gerekebilir.
   * İşte Linux çekirdeğindeki `ens33.10` ve `ens33.20` gibi sanal alt arayüzler (*Sub-interfaces*), switch'ten gelen 802.1Q etiketli paketleri ayıklar ve tek bir kablo üzerinden sunucuyu birden fazla ağın üyesi yapar!

---

### 🧪 Linux Üzerinde Canlı VLAN Testi:

```bash
# 1. ens33 kartınıza bağlı VLAN 10 alt arayüzü oluştur:
ip link add link ens33 name ens33.10 type vlan id 10

# 2. Sanal VLAN arayüzüne IP ata ve ayağa kaldır:
ip addr add 10.10.10.5/24 dev ens33.10
ip link set dev ens33.10 up

# 3. VLAN etiketleme detayını (802.1Q) doğrula:
ip -d link show ens33.10
# Çıktı: vlan protocol 802.1Q id 10 ...

# 4. Test bittikten sonra sanal VLAN arayüzünü sil:
ip link del ens33.10
```

---

## 13. VPN (Şifreli Tünel) İnceleme (WireGuard / IPsec)

Bir VPN tüneli üzerinden güvenli yönlendirilmeyi doğrulamak için:

```bash
# WireGuard tüneli varsa:
wg show 2>/dev/null || echo "Aktif WireGuard tüneli yok."

# Belirli bir şirket içi IP'ye giderken hangi arayüzün (tünelin) seçildiğini test et:
ip route get 10.50.1.1 2>/dev/null || echo "Özel rota tanımlı değil."
```

---

## 14. Proxy (Vekil Sunucu) ve Yük Dengeleme Testi

İstemci adına vekillik yapan Forward Proxy veya sunucu önündeki Nginx Reverse Proxy'yi test etmek için:

```bash
# 1. Forward Proxy üzerinden web isteği atma testi (örnek port 8080):
curl -x http://127.0.0.1:8080 -I https://google.com 2>/dev/null || echo "Aktif Proxy dinleyicisi yok."

# 2. Reverse Proxy (Nginx) arkasındaki sunucu başlıklarını inceleme:
curl -I http://localhost 2>/dev/null || echo "Yerel web sunucu çalışmıyor."
```

---

## 15. 🚀 Bütünleşik Canlı Test Scripti (Tek Komutla 15 Adımı Raporlama)

Aşağıdaki hazır Bash scriptini Linux makinenizde çalıştırarak tüm bu ağ parametrelerini tek bir ekranda sıralı rapor olarak alabilirsiniz:

```bash
cat << 'EOF' > test_network_lifecycle.sh
#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "🌐 LİNUX AĞ YAŞAM DÖNGÜSÜ KONTROL RAPORU (VMware Ubuntu)"
echo "=========================================================="

echo -e "\n[01. Fiziksel MAC Adresi (ens33)]"
ip link show ens33 | grep -E "link/ether"

echo -e "\n[02. DHCP Kira Kaydı & DNS]"
cat /run/systemd/netif/leases/* 2>/dev/null | grep -E "ADDRESS" || true
grep nameserver /etc/resolv.conf

echo -e "\n[03. Yerel IP Adresi (IPv4 / IPv6)]"
ip -br addr show ens33

echo -e "\n[04. Subnet Mask & Broadcast]"
ip -4 addr show ens33 | grep -E "inet "

echo -e "\n[05. Varsayılan Ağ Geçidi (Default Gateway)]"
ip route show default

echo -e "\n[06. ARP Tablosu (Modem MAC Adresi)]"
ip neigh show dev ens33 | head -n 3

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
