# 🛡️ Faz 5: Katman 7 Yük Dengeleme, Reverse Proxy & X-Forwarded-For

Ana rehberimizin 6. modülünde açıklanan en kritik kurumsal ağ senaryosuna hoş geldiniz:  
> *"Nginx Reverse Proxy arkasında 2 adet backend sunucusu çalışırken; yük bu sunuculara nasıl dengelenir? Ve backend sunucusu gelen isteğin Nginx'ten değil de Ahmet'in gerçek IP'sinden (`10.20.1.45`) geldiğini nereden anlar?"*

Bu laboratuvarda; **Nginx**'i `least_conn` algoritması ile bir **Reverse Proxy / Load Balancer** olarak yapılandıracak, arkasında çalışan 2 adet Python backend servisine istekleri dağıtacak ve **`X-Forwarded-For`** başlığının adli bilişim ve kimlik takibindeki hayati rolünü canlı JSON çıktılarıyla kanıtlayacağız!

---

## 📌 Teorik Bağlantı (Ana Rehber)
Bu lab aşağıdaki rehber bölümlerini uygulamaya döker:
* [Modül 5 / Madde 14: Proxy (Forward vs Reverse Proxy)](../../README.md#14-proxy-vekil-sunucu)
* [Modül 6 / 4. Aşama: Nginx Yapılandırması ve X-Forwarded-For Önemi](../../README.md#4-aşama-sunucu-odasında-karşılama-ve-yük-dağıtımı-reverse-proxy---nginx--haproxy)

---

## 🏗️ Laboratuvar Mimarisi

```text
[ ahmet-pc ] (10.20.1.45)
     │
     │ HTTP İsteği: http://10.20.1.50 (Port 80)
     ▼
[ nginx-proxy ] (10.20.1.50)
  │ (least_conn Yük Dengeleme)
  │ ➕ Eklenen Başlık: X-Real-IP: 10.20.1.45
  │
  ├──► [ backend-1 ] (10.20.1.61:3000) ── "Kayıt Servisi"
  └──► [ backend-2 ] (10.20.1.62:3000) ── "Raporlama Servisi"
```

---

## 🚀 Laboratuvarı Başlatma

Terminalinizi bu klasörde (`labs/phase-05-reverse-proxy-cluster`) açın:

```bash
docker compose up -d
```

Container'ların hazır olduğunu teyit edin:
```bash
docker compose ps
```

---

## 🔍 Adım Adım İnceleme ve Deneyler

### 1. Adım: Yük Dağıtımını Canlı İzleme
Ahmet'in bilgisayarından Nginx'e peş peşe 4 kez istek atarak yükün nasıl paylaştırıldığını görelim:

#### 🔹 1. Yol: Container İçine Girerek (Tavsiye Edilen - Windows & Linux Uyumlu)
Windows CMD veya PowerShell'de `grep` ve döngü komutlarının tırnak/boru (`|`) hatası vermemesi için en temiz ve garantili yöntem doğrudan container terminaline bağlanmaktır:

```bash
# 1. Ahmet'in container kabuğuna (Linux terminali) bağlanın:
docker exec -it ahmet-pc sh

# 2. Container içinde peş peşe 4 istek gönderin:
for i in 1 2 3 4; do curl -s http://10.20.1.50 | grep "served_by"; sleep 0.5; done
```

*(İşiniz bitince çıkmak için `exit` yazabilirsiniz; ancak 2. ve 3. adımları da doğrudan bu açık terminalden çalıştırabilirsiniz).*

#### 🔹 2. Yol: Dış Terminalden (Tek Satırda)
Eğer container içine girmeden doğrudan Windows terminalinizden çalıştırmak isterseniz:
* **Windows CMD (Komut İstemi) için:**
  ```cmd
  docker exec ahmet-pc sh -c "for i in 1 2 3 4; do curl -s http://10.20.1.50 | grep served_by; sleep 0.5; done"
  ```
* **PowerShell için:**
  ```powershell
  1..4 | ForEach-Object { docker exec ahmet-pc curl -s http://10.20.1.50 | Select-String "served_by"; Start-Sleep -Milliseconds 500 }
  ```

#### 📋 Örnek Çıktı:
```text
  "served_by": "backend-01 (Kayıt Servisi)",
  "served_by": "backend-02 (Raporlama Servisi)",
  "served_by": "backend-01 (Kayıt Servisi)",
  "served_by": "backend-02 (Raporlama Servisi)",
```
🎉 Görüldüğü gibi Ahmet tek bir IP adresine (`10.20.1.50`) gitmektedir; ancak Nginx istekleri arkadaki iki sunucuya sırayla ve adilce paylaştırmaktadır!

---

### 2. Adım: `X-Forwarded-For` ve `X-Real-IP` Kanıtı
Şimdi tek bir isteğin tüm detaylı JSON çıktısını inceleyelim:

```bash
docker exec -it ahmet-pc curl -s http://10.20.1.50
```

#### 📋 JSON Çıktısı:
```json
{
  "status": "success",
  "served_by": "backend-01 (Kayıt Servisi)",
  "analiz": {
    "dogrudan_baglanan_ip (Nginx)": "10.20.1.50",
    "gercek_kullanici_ip (X-Real-IP)": "10.20.1.45",
    "proxy_zinciri (X-Forwarded-For)": "10.20.1.45",
    "istenen_host": "10.20.1.50"
  },
  "mesaj": "Tebrikler! İstek Nginx üzerinden 'backend-01 (Kayıt Servisi)' sunucusuna iletildi."
}
```

🔍 **Kritik Güvenlik Analizi:**
* **`dogrudan_baglanan_ip`**: Backend sunucusuna TCP seviyesinde bağlanan IP **`10.20.1.50` (Nginx)**'dir.
* **`gercek_kullanici_ip`**: Eğer Nginx `proxy_set_header X-Real-IP $remote_addr;` kuralını yazmasaydı, backend sunucusu Ahmet'in kim olduğunu **asla bilemezdi!**
* Bu başlık sayesinde backend yazılımı, muhasebe işlemini yapanın **Ahmet (`10.20.1.45`)** olduğunu loglara kaydedebilir.

---

### 3. Adım: Yüksek Erişilebilirlik (High Availability / Failover) Testi
Peki arkadaki backend sunucularından biri çökerse ne olur?

`backend-1` sunucusunu kapatalım:
```bash
docker stop backend-1
```

Şimdi Ahmet tekrar istek atsın:

#### 🔹 1. Yol (Ahmet'in açık terminalinden):
```bash
curl -s http://10.20.1.50 | grep "served_by"
```

#### 🔹 2. Yol (Windows Dış Terminalinden):
```cmd
docker exec ahmet-pc sh -c "curl -s http://10.20.1.50 | grep served_by"
```

#### 📋 Sonuç:
İstek anında **`backend-02 (Raporlama Servisi)`** tarafından karşılanır! Ahmet herhangi bir hata kodu (`502 Bad Gateway`) veya kesinti görmez. Nginx çöken sunucuyu otomatik algılayıp trafiği ayakta kalan sunucuya yönlendirmiştir (**Zero-Downtime**).

Sunucuyu tekrar ayağa kaldıralım:
```bash
docker start backend-1
```

---

## 🧹 Laboratuvarı Kapatma ve Temizlik

```bash
docker compose down
```

---

## 🎯 Bu Fazda Ne Öğrendik?
1. Katman 7'de çalışan bir **Reverse Proxy**'nin sunucu kümesinin önünde bir kalkan görevi gördüğünü,
2. **Yük Dengeleme (Load Balancing)** algoritmalarının nasıl çalıştığını,
3. Vekil sunucuların ardındaki gerçek istemci IP'sinin **`X-Forwarded-For`** ve **`X-Real-IP`** HTTP başlıkları ile nasıl taşındığını,
4. Arka sunuculardan biri kapandığında Nginx'in otomatik hata toleransı sağladığını (**Failover**).

Son laboratuvarımız: [**Faz 6: Canlı Paket Analizi (Deep Packet Inspection & tcpdump)**](../phase-06-packet-analysis/)! 🚀
