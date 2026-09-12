# 🔬 Faz 6: Canlı Paket Analizi (tcpdump & TCP 3-Way Handshake)

Ağ mühendisliğinin en heyecan verici anı, teoride gördüğünüz bayrakların (**SYN, SYN-ACK, ACK, FIN, RST**) kablo üzerinden geçerken gerçek halini yakaladığınız andır!

Bu laboratuvarda; **`tcpdump`** aracını kullanarak istemci ile sunucu arasındaki TCP el sıkışmasını, HTTP veri iletimini ve kapalı bir porta gidildiğinde dönen **RST (Reset)** paketini terminalde mikroskobik düzeyde analiz edeceğiz.

---

## 📌 Teorik Bağlantı (Ana Rehber)
Bu lab aşağıdaki rehber bölümlerini uygulamaya döker:
* [Modül 3 / Madde 8: TCP & UDP (3-Way Handshake Diyagramı)](../../README.md#8-tcp--udp)
* [Modül 2 / Madde 5: ARP Protokolü](../../README.md#5-arp-address-resolution-protocol)
* [Modül 3 / Madde 9: Portlar ve Sockets](../../README.md#9-portlar-ve-sockets)

---

## 🏗️ Laboratuvar Mimarisi

```text
[ client-pc ] (10.30.1.45)
  └── tcpdump dinleyicisi (eth0)
       │
       │ 1. [SYN]       ──►
       │ 2. ◄── [SYN, ACK]
       │ 3. [ACK]       ──► (Bağlantı Kuruldu!)
       │ 4. [P.] (HTTP) ──►
       ▼
[ target-web ] (10.30.1.50 - Nginx Port 80)
```

---

## 🚀 Laboratuvarı Başlatma

Terminalinizi bu klasörde (`labs/phase-06-packet-analysis`) açın:

```bash
docker compose up -d
```

---

## 🔍 Adım Adım İnceleme ve Deneyler

### 1. Adım: Birinci Terminalde `tcpdump` Dinleyicisini Başlatma
Paketleri anlık olarak ekrana basmak için `client-pc` içinde bir paket yakalayıcı başlatalım:

```bash
docker exec -it client-pc tcpdump -nn -i eth0 -v 'tcp or arp'
```
*(Bu terminal dinlemede bekleyecektir; kapatmayın).*

---

### 2. Adım: İkinci Terminalden İstek Atma (TCP El Sıkışması)
**İkinci bir terminal penceresi açın** ve sunucuya tek bir HTTP isteği gönderin:

```bash
docker exec -it client-pc curl -s http://10.30.1.50 > /dev/null
```

Şimdi birinci terminaldeki `tcpdump` ekranına dönün! Gözlerinizin önünde şu tarihî akış gerçekleşmiştir:

#### 📋 Adım Adım Paket Analizi:

```text
1. PAKET (SYN):
IP 10.30.1.45.41280 > 10.30.1.50.80: Flags [S], seq 349120194, win 64240, ...
==> Ahmet sunucuya der ki: "Seninle 80 portundan konuşmak istiyorum! Benim Sequence Numaram: 349120194"

2. PAKET (SYN-ACK):
IP 10.30.1.50.80 > 10.30.1.45.41280: Flags [S.], seq 812940122, ack 349120195, ...
==> Nginx cevap verir: "İsteğini aldım (ack=seq+1), ben de hazırım! Benim Sequence Numaram: 812940122"

3. PAKET (ACK):
IP 10.30.1.45.41280 > 10.30.1.50.80: Flags [.], ack 812940123, win 502, ...
==> Ahmet onaylar: "Senin numaranı da aldım! Artık bağlantı resmi olarak kuruldu (ESTABLISHED)!"

4. PAKET (HTTP GET Verisi - PUSH):
IP 10.30.1.45.41280 > 10.30.1.50.80: Flags [P.], seq 1:78, ack 1 ...
==> "GET / HTTP/1.1" metni sunucuya teslim edilir.

5. PAKET (FIN-ACK - Bağlantıyı Kapatma):
IP 10.30.1.45.41280 > 10.30.1.50.80: Flags [F.], seq 78, ack 612 ...
==> İstek bitti, oturum temiz bir şekilde kapatılır.
```

---

### 3. Adım: Kapalı Porta İstek Atma ve `[RST]` (Reset) Bayrağını Görme
Eğer sunucuda açık olmayan rastgele bir porta (örneğin port `9999`) bağlanmaya çalışırsak ne olur?

İkinci terminalden çalıştırın:
```bash
docker exec -it client-pc nc -zv 10.30.1.50 9999
```

#### 📋 `tcpdump` Ekranındaki Yanıt:
```text
IP 10.30.1.45.54120 > 10.30.1.50.9999: Flags [S] ...
IP 10.30.1.50.9999 > 10.30.1.45.54120: Flags [R.], seq 0, ack 1 ...
```

* **`Flags [R.]` (RST)**: Sunucunun işletim sistemi çekirdeği anında bir **RST (Reset)** paketi fırlatarak *"Bu portta dinleyen hiçbir uygulama yok, kapı kilitli!"* der ve bağlantıyı anında reddeder (`Connection refused`).

---

### 4. Adım: Paketleri `.pcap` Dosyası Olarak Kaydedip Wireshark ile İnceleme
Dilerseniz paketleri ekrana basmak yerine profesyonel analiz aracı olan **Wireshark**'ta incelemek üzere bir `.pcap` dosyasına yazdırabilirsiniz:

```bash
docker exec -it client-pc tcpdump -i eth0 -w /captures/handshake.pcap
```
İstek attıktan sonra `Ctrl+C` ile durdurun.  
Proje klasörünüzdeki `labs/phase-06-packet-analysis/captures/handshake.pcap` dosyası oluşacaktır. Bu dosyayı çift tıklayarak bilgisayarınızdaki **Wireshark** programıyla açabilir; renkli paket akışını ve TCP el sıkışma grafiğini grafik arayüzde inceleyebilirsiniz!

---

## 🧹 Laboratuvarı Kapatma ve Temizlik

```bash
docker compose down
```

---

## 🎯 Bu Fazda Ne Öğrendik?
1. TCP protokolünün bağlantı kurarken kullandığı **3-Way Handshake (SYN, SYN-ACK, ACK)** sürecini canlı yakalamayı,
2. İletilen verilerin **Push (`[P.]`)** bayrağıyla gönderildiğini,
3. Kapalı bir porta erişildiğinde işletim sisteminin **Reset (`[R.]`)** bayrağı ile bağlantıyı nasıl kestiğini,
4. **`tcpdump`** ve **Wireshark** ile paket yakalayıp profesyonel ağ analizi yapmayı.

Tebrikler! 6 fazlık kapsamlı ağ laboratuvar serisini başarıyla tamamladınız! 🎉
