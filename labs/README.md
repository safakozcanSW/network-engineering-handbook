# 🧪 Uygulamalı Docker Ağ Laboratuvarları (Network Hands-on Labs)

Bu dizin, ana [README.md](../README.md) el kitabında anlatılan tüm teorik ağ kavramlarını (**MAC, IP, Subnetting, Default Gateway, ARP, DHCP, DNS, TCP/UDP, NAT, VLAN/İzolasyon, Firewall, Proxy ve Paket Analizi**) kendi bilgisayarınızda **adım adım, sıfırdan ileri seviyeye** canlı olarak test edebilmeniz için tasarlanmış uygulamalı laboratuvar serisidir.

---

## 🗺️ Laboratuvar Yol Haritası (Fazlar)

Her laboratuvar bağımsız bir klasörde yer alır; kendi `docker-compose.yml` dosyasını ve her komutun ekran çıktısını detaylandıran bir kılavuz (`README.md`) içerir:

| Faz | Konu & Başlık | Öğrenilecek Temel Kavramlar | İlgili Rehber Modülü |
| :--- | :--- | :--- | :--- |
| [**Faz 1**](./phase-01-basics-and-isolation/) | **Ağ Temelleri, Alt Ağlar & İzolasyon** | Bridge ağı, veth, MAC adresi, Subnet Mask (/24), ARP tablosu, Yerel ağ izolasyonu | Modül 1 (Madde 1, 2, 3) & Modül 2 (Madde 5) |
| [**Faz 2**](./phase-02-routing-and-gateway/) | **Yönlendirme & Inter-VLAN Gateway** | Çok bacaklı Router, `ip_forward`, Yönlendirme tablosu (`ip route`), Default Gateway, Traceroute | Modül 1 (Madde 4) & Modül 4 (Madde 11) |
| [**Faz 3**](./phase-03-nat-and-port-mapping/) | **Docker NAT & Port Yönlendirme** | Port Mapping (`-p`), DNAT (Hedef NAT), SNAT (Masquerade), `iptables` NAT tabloları | Modül 4 (Madde 10) |
| [**Faz 4**](./phase-04-custom-dns-resolver/) | **Şirket İçi Özel DNS Çözümleme** | CoreDNS, `sirket.local` bölgesi, A & CNAME kayıtları, `/etc/resolv.conf`, `dig` ve `nslookup` | Modül 2 (Madde 7) |
| [**Faz 5**](./phase-05-reverse-proxy-cluster/) | **Reverse Proxy & Yük Dengeleme** | Nginx Reverse Proxy, `least_conn` algoritması, SSL/TLS sonlandırma, `X-Forwarded-For` başlığı | Modül 5 (Madde 14) & Modül 6 |
| [**Faz 6**](./phase-06-packet-analysis/) | **Canlı Paket Analizi (Deep Inspection)** | `tcpdump`, TCP 3-Way Handshake (SYN, SYN-ACK, ACK), FIN/RST bayrakları, Wireshark PCAP analizi | Modül 3 (Madde 8) |

---

## 💻 Ön Gereksinimler

Laboratuvarları çalıştırmak için sisteminizde yalnızca şunların yüklü olması yeterlidir:
1. **Docker Desktop** (Windows / macOS) veya **Docker Engine** (Linux)
2. **Docker Compose** (Docker ile birlikte varsayılan olarak gelir: `docker compose version`)

Terminalinizin çalıştığını doğrulamak için:
```bash
docker --version
docker compose version
```

---

## 🎯 Her Laboratuvarda İzlenen Standart Metot

Her faz kılavuzunda şu 4 soru eksiksiz olarak cevaplanır:
1. **Ne Yapıyoruz?** (Rehberdeki teorik arkaplan ve senaryo)
2. **Nasıl Yapıyoruz?** (Çalıştırılacak Docker Compose ve yapılandırmalar)
3. **Nereden Bakıyoruz?** (Hangi terminal komutu ile hangi tablonun incelendiği)
4. **Çıktı Ne Anlama Geliyor?** (Terminalde gördüğünüz satırların mühendislik yorumu)

İlk laboratuvar olan [**Faz 1: Ağ Temelleri, Alt Ağlar & İzolasyon**](./phase-01-basics-and-isolation/) ile başlayabilirsiniz! 🚀
