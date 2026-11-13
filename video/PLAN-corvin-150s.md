# Rencana: Corvin — film teknis 2:30 untuk juri

Status: **Dibangun (14 Nov 2026)**: komposisi `CorvinTech` di `src/tech/`, render `npm run render:tech` →
`out/corvin-tech.mp4`. Perubahan dari draft di bawah: intro dipercepat jadi **8 s**, budget ditulis **≈ USD 333**,
SFX + musik dari pack user (`public/sfx/`, `public/music/`, kredit di `public/sfx/CREDITS.csv`), cue sheet
`sfx-cues.csv` (`npm run cues:tech`). Waktu scene final ada di `src/tech/timeline.ts` (`TS`).
Sumber konteks: spec **v0.1.31** di `origin/main` (00–04), `docs/review/project-overview.md`, poster A2 dan
deck Senior Referee Review.

## 1. Tujuan

Film tanpa voice-over, berdurasi **150 s**, dengan musik latar dan SFX. Tujuannya menjelaskan Corvin kepada juri:
apa yang dikerjakan robot, **bagian-bagiannya beserta alasan desain singkat**, kelistrikan dan suplai daya,
manufaktur, lalu satu simulasi swap penuh. Setiap layar harus bisa dipakai sebagai alat bantu saat menjawab
pertanyaan juri ("bagaimana implementasinya? bagaimana geraknya?").

Kriteria juri (spec 00 §1): Innovation, Technical Viability, Impact & Sustainability, Communication.

## 2. Yang berubah dari film pitch 90 s

| Film 90 s (lama) | Film 150 s (baru) |
|---|---|
| Dibuka dengan hook "ruang server gelap" dan problem | **Langsung dibuka dengan perkenalan Corvin**. Hook dan problem dipotong |
| Palet oranye | **Palet biru** (lihat §5) |
| Fitur hanya disebut singkat (6 × 3 s) | Penjelasan per subsistem, dengan angka spec dan **alasan desain** |
| Tidak ada power, manufaktur, atau elektronik detail | Ada scene khusus power tree, safety, motion board, dan manufaktur / packing |
| Swap di arena 3,2 m dengan belokan L | **Tetap 3,2 m + belokan L** (Q1), alur langkah mengikuti spec 00 §6 |
| Penutup "< $500" | Budget terbaru **≈ Rp 6 juta** (Q10) |
| Delta PLC + tower light | **ESP32 rack controller** (Modbus TCP) + **Delta 24 V PSU** + panel lamp R/Y/G (Q2) |
| Nama "RackBot" di beberapa tempat | Semua **Corvin** |

Model 3D tetap desain yang sama, tetapi **diekspor ulang dari CAD v0.1.31** (Q3) dan dipecah per subsistem
(chassis, roda, Z mast + lead screw, tray, Y rail + carriage, finger, elektronik, baterai) untuk exploded view.

## 3. Struktur (150 s = 4500 frame @ 30 fps; musik 120 BPM, 1 bar = 2 s = 60 frame)

| # | Waktu | Scene | Visual | Isi teks layar (ringkas) |
|---|---|---|---|---|
| 1 | 0:00–0:12 | **Perkenalan Corvin** | Logo atau nama muncul dari garis biru, robot turntable di studio gelap kebiruan | "Corvin" · "Making drive replacement easier" · Delta Cup 2026 · Automation track · Boys Go to Thailand · Brawijaya University |
| 2 | 0:12–0:26 | **Sistem dalam satu layar** | Kamera naik: rack 1 × 4 bay, spare station (home dan charging), robot di antaranya. Garis Wi-Fi beranimasi | Peran tiap bagian: robot (Pi + motion board), rack controller (Modbus TCP), dashboard. "1 job = spare → rack → spare" |
| 3 | 0:26–0:40 | **Base dan drive** | Exploded view base (deck naik, roda keluar), callout | 2020 V-slot · 2 × NEMA17 direct drive · roda Ø80 PETG + TPU · 150 / 50 mm/s · *kenapa:* tanpa belt, step open-loop repeatable, satu jenis driver |
| 4 | 0:40–0:54 | **Z lift dan tray 2 slot** | Mast naik-turun, highlight lead screw, tray 2 slot dengan pitch 45 mm | 2040 mast · Tr8×2 lead screw (self-locking) · Z 102–295 mm · *kenapa 2 slot:* satu kunjungan = cabut + pasang |
| 5 | 0:54–1:08 | **Y extractor dan finger** | Close-up: Y carriage maju, finger servo berputar masuk ke notch, tarik, dorong | GT2 belt · stroke 177 mm · MG90S finger swing · *kenapa:* tanpa gaya jepit, tidak ada bagian yang melewati muka rack, ±1 mm play |
| 6 | 1:08–1:20 | **Vision dan docking** | Frustum kamera, AprilTag menyala, V-funnel menuntun robot | IMX708 120° · AprilTag approach + cek ID caddy · V-funnel ±2 mm + dock switch |
| 7 | 1:20–1:38 | **Elektronik dan power** | Diagram power tree beranimasi (aliran energi berupa partikel biru), lalu motion board PCB | 4S 18650 50,4 Wh · BMS · fuse 7,5 A · INA226 · E-stop relay memutus VMOT · buck 5,15 V Pi / 5,8 V servo · dock 24 V Delta PSU → CC/CV 16,8 V 1,5 A · ESP32-S3 + 4 × TMC2209, PCB 100 × 100 JLCPCB · ≈ 0,6–1,0 Wh per swap |
| 8 | 1:38–1:48 | **Safety dan rack** | Rack dari belakang: PSU, controller, lampu R/Y/G, E-stop | Watchdog 2 s · dock bertegangan hanya saat docked · E-stop memutus daya secara hardware · Modbus register map |
| 9 | 1:48–2:14 | **Simulasi swap penuh** | Alur spec 00 §6 (7 langkah) dipercepat, dengan step list, panel bay, dan mission clock | Pick spare → undock dan putar 180° → dock → extract (cek tag ID) → insert → kembali → RMA → charge · cycle sim ≈ 107 s (target ≤ 3 min) |
| 10 | 2:14–2:24 | **Manufaktur dan logistik** | Part terbang ke posisi flat-pack, lalu 4 tas kabin | Part cetak PETG / PLA / TPU (print service, bed 400 mm) · V-slot dipotong · PCB JLCPCB (SMD assembled) · ≈ 14 kg dalam 4 tas × 7 kg · battery < 100 Wh · whole system ≈ Rp 6 M |
| 11 | 2:24–2:30 | **Penutup** | Robot docked dan charging, logo | ≤ 3 min/swap · ≥ 95 % / 50 cycle (target) · ≈ 50 Wh · Delta inside · nama tim |

Semua angka diambil dari spec. Target (cycle time, success rate) diberi label **target**, dan clock diberi label
**simulated**.

## 4. Teknik motion design

- **Exploded view** dan isolasi subsistem: bagian lain dibuat transparan atau ghosted, subsistem yang dibahas
  diberi warna dan glow biru.
- **Callout leader-line** yang menempel di titik 3D, diproyeksikan ke layar setiap frame, sehingga tidak meleset
  saat kamera bergerak.
- **Diagram 2D beranimasi** (power tree, sistem, Wi-Fi) digambar SVG di Remotion, dengan garis yang
  "menggambar dirinya" dan partikel aliran energi.
- **Spec card** dengan count-up angka dan layout kartu yang konsisten di semua scene.
- Transisi tegas di bar musik. Kamera bergerak pelan, potongan keras di downbeat, tanpa whip.
- Resolusi render 1920 × 1080 (opsi 4K, Q8).

## 5. Gaya visual (biru)

Usulan, diambil dari palet poster A2:

| Token | Hex | Pakai untuk |
|---|---|---|
| bg | `#071827` / `#0f2a3f` | Latar navy |
| accent | `#38d3ff` | Highlight utama, garis, glow |
| accent-2 | `#5aa0ff` | Elemen sekunder, diagram |
| ok | `#3ddc8f` | Status OK atau charging |
| fault | `#ff7a59` | Hanya untuk drive rusak dan E-stop |
| text | `#e8f1f8` / `#c4d6e4` | Teks |

## 6. Audio (tanpa voice-over)

- **Musik latar:** 150 s, 120 BPM, electronic / tech yang "bersih". Pilihannya prosedural (dibuat dengan
  Python seperti `audio/make_bed.py`, bebas lisensi) atau track royalty-free dari Anda (Q6).
- **SFX** disinkronkan ke event animasi: whoosh di transisi, "tick" UI saat callout muncul, dengung stepper
  saat roda / Z / Y bergerak, klik servo saat finger engage, klik microswitch saat dock, chime saat job selesai,
  dan dengung listrik halus di scene power. SFX dibuat prosedural (numpy / scipy), lalu di-mix dan diberi
  ducking terhadap musik.

## 7. Skill dan tool

- **`remotion-dev/skills@remotion-best-practices`**: skill resmi Remotion (≈ 812K install). Isinya pola animasi,
  sequencing, audio, dan performa render. Usul dipasang global (`npx skills add remotion-dev/skills@remotion-best-practices -g -y`).
- SFX: `elevenlabs/skills@sound-effects` (15K install) butuh API key ElevenLabs yang berbayar. Rekomendasinya
  SFX prosedural saja (gratis, deterministik, dan bisa disinkronkan per frame).

## 8. Implementasi (setelah rencana disetujui)

1. Rebase / merge pekerjaan ke `origin/main` terbaru, karena main sudah mengganti judul ke Corvin
   (83942c9) dan spec sudah v0.1.31.
2. Komposisi baru `CorvinTech` (150 s) di `src/tech/`, berdampingan dengan `RackBotPitch` (film 90 s tetap ada).
   Script / keyframe engine `anim.ts` dan `camera.ts` dipakai ulang.
3. Token warna biru dan komponen UI baru: spec card, callout 3D, diagram SVG.
4. Engine swap dibuat ulang mengikuti tata letak spec.
5. Audio: `audio/make_tech_bed.py` (musik + SFX dari daftar event yang diekspor oleh timeline).
6. Verifikasi: contact sheet tiap scene, scan kontinuitas (kamera dan caddy) seperti sebelumnya,
   serta pengecekan setiap angka di layar terhadap spec.
7. Render, kompres ≤ 15 MB untuk deck jika diperlukan.

Perkiraan: plan → storyboard frame kunci (contact sheet) untuk disetujui → film penuh.

## 9. Keputusan (hasil grill)

| # | Topik | Keputusan |
|---|---|---|
| Q1 | Arena | **Tetap 3,2 m + belokan L** (seperti film 90 s). Spec demo memakai 700 mm, jadi teks tidak menyebut jarak |
| Q2 | Rack controller | **ESP32 fallback** (Modbus TCP, register map identik, siap diganti Delta PLC). Delta tetap ada lewat **Delta 24 V PSU** (LYTE II DRL-24V120W1EN). Status lamp = panel lamp R/Y/G, bukan tower light |
| Q3 | Model 3D | **Ekspor ulang GLB dari CAD v0.1.31**, dipecah per subsistem untuk exploded view |
| Q4 | Hasil uji | **Semua masih target.** Cycle time dan success rate diberi label "target", clock diberi label "simulated" |
| Q5 | Palet | **Biru poster A2** (§5) |
| Q6 | Bahasa | **English** |
| Q7 | Audio | **User mencari sendiri SFX-nya** dari daftar §10 |
| Q8 | Intro | Corvin + **Boys Go to Thailand · Brawijaya University** + tagline **"Making drive replacement easier"** |
| Q9 | Musik | **User yang mencarikan** (§10.E). Draft memakai click-track 120 BPM agar cut tetap di bar |
| Q10 | Budget | **≈ Rp 6 juta** (angka terbaru dari user, menggantikan forecast 575 USD di spec). Ditulis "whole system ≈ Rp 6 M"; konversi USD dicek ulang di storyboard |
| Q11 | Alur | **Storyboard dulu** (contact sheet frame kunci per scene) → persetujuan → film penuh 1080p |
| Q12 | Skill | `remotion-best-practices` terpasang global (14 Nov), sudah direview: isinya router ke referensi Remotion |

## 10. Daftar SFX (untuk dicarikan)

**Format file:** WAV 48 kHz (16- atau 24-bit). Mono untuk SFX mekanik, stereo untuk whoosh, riser, dan ambience.
Beri jarak minimal (< 20 ms) sebelum transient. Nama file sesuai kolom **ID** (misalnya `sfx_02_whoosh_soft.wav`).
Cari **variasi 2–3 take** untuk SFX yang berulang (tanda ×), supaya tidak terdengar copy-paste.
Lisensi harus royalty-free atau CC0 untuk kompetisi publik (catat sumbernya).

Rekomendasi sumber: Freesound (filter CC0), Pixabay SFX, Sonniss GDC bundle (gratis), Zapsplat, BOOM Library
(berbayar, sangat unik), Epidemic / Artlist (berlangganan).

### A. Transisi dan UI (motion graphics)

| ID | Nama | Dipakai di | Durasi | Karakter (supaya tidak basic) | Kata kunci pencarian |
|---|---|---|---|---|---|
| sfx_01 | Logo reveal / impact | Intro 0:00–0:04, nama Corvin muncul | 2–3 s | Sub-boom dalam + kilau digital tinggi (shimmer), ekor reverb panjang, bukan "cinematic boom" generik | `logo reveal tech shimmer`, `sub drop glitch`, `digital impact airy` |
| sfx_02 × 3 | Whoosh halus | Setiap pergantian scene (≈ 10 kali) | 0,4–0,8 s | Udara + sedikit tekstur digital / granular, tidak "swoosh kartun" | `air whoosh soft tech`, `granular swish`, `transition whoosh subtle` |
| sfx_03 | Riser | Sebelum simulasi swap (1:44–1:48) | 3–4 s | Riser bernada naik dengan noise filter sweep, berakhir tanpa hit | `tension riser electronic`, `filter sweep riser` |
| sfx_04 × 3 | UI tick / blip | Callout dan label muncul (≈ 40 kali) | 50–120 ms | Klik digital kering, bernada tinggi, sangat pendek. Variasi pitch | `ui click minimal`, `hud blip`, `interface tick futuristic` |
| sfx_05 | Data / scan sweep | Garis callout menggambar diri, kamera vision scan | 0,5–1 s | Glitchy data chatter / scanning beep | `data scan hud`, `scanner sweep sci-fi`, `digital processing` |
| sfx_06 | Number count-up | Kartu angka (50,4 Wh, 177 mm, …) | 0,5–1 s | Ticker digital cepat dengan pitch naik | `counter ticking digital`, `number roll ui` |
| sfx_07 | Panel / card slide | Spec card dan step list masuk | 0,3 s | Slide plastik / kaca halus | `ui panel slide`, `glass swipe` |
| sfx_08 | Exploded view separation | Bagian robot memisah (scene 3–5) | 1–1,5 s | Klik magnetis + whoosh logam ringan, terasa "presisi" | `mechanical separate magnetic`, `metal parts assemble whoosh` |
| sfx_09 | Reassemble / snap-back | Bagian kembali menyatu | 0,5–1 s | Kebalikan sfx_08, diakhiri "snap" | `parts snap together`, `mechanical lock click` |

### B. Mekanik robot (disinkronkan dengan gerak)

| ID | Nama | Dipakai di | Durasi | Karakter | Kata kunci |
|---|---|---|---|---|---|
| sfx_10 | Stepper motor drive (loop) | Robot berjalan (scene 9, belokan L) | loop 3–5 s | Dengungan stepper / pita nada **bersih** (TMC2209 = senyap, jadi halus, bukan dengungan kasar) + roda di lantai | `stepper motor whine`, `small robot driving loop`, `3d printer stepper hum` |
| sfx_11 | Stepper start / stop | Awal dan akhir setiap gerakan drive | 0,3 s | Ramp up / down nada | `motor spin up short`, `servo stop` |
| sfx_12 | Lead screw lift (loop) | Z lift naik-turun (scene 4, 9) | loop 2–3 s | Nada stepper lebih rendah + gesekan ulir halus | `lead screw motor`, `linear actuator`, `cnc z axis` |
| sfx_13 | Belt slide (Y extractor) | Y maju-mundur (scene 5, 9) | 1–1,5 s | Desis belt GT2 + rolling V-wheel, cepat | `belt drive slide`, `linear rail carriage`, `3d printer belt move` |
| sfx_14 × 2 | Servo swing | Finger engage / park (≈ 10 kali) | 0,2–0,4 s | Servo kecil "zzt" bernada tinggi, gear plastik | `micro servo`, `sg90 servo sound`, `small servo whir` |
| sfx_15 × 2 | Caddy slide in/out | Caddy ditarik / didorong di bay | 0,5–0,8 s | Plastik keras bergesek di rel plastik | `plastic drawer slide`, `server drive tray slide` |
| sfx_16 | Caddy seated click | Caddy terpasang penuh di bay / slot | 0,15 s | Klik plastik solid "terkunci" | `plastic click latch`, `hard drive tray click` |
| sfx_17 | Microswitch click | Dock switch / bay switch aktif | 0,05 s | Klik microswitch lever, sangat kecil | `microswitch click`, `limit switch` |
| sfx_18 | Dock contact | Robot masuk V-funnel (dock rack dan base) | 0,4 s | Benturan plastik lembut + klik + "thunk" halus | `robot docking`, `soft mechanical thud` |

### C. Elektrik dan sistem

| ID | Nama | Dipakai di | Durasi | Karakter | Kata kunci |
|---|---|---|---|---|---|
| sfx_19 | Power-up / boot | Scene power: energi mulai mengalir dari baterai | 1,5–2 s | Electric hum yang naik + kilau, bukan "Windows startup" | `power up electric hum rise`, `sci-fi power on` |
| sfx_20 | Electric flow (loop) | Partikel energi di power tree | loop 4–6 s | Dengung listrik halus / plasma tipis, low volume | `electric current loop`, `energy hum subtle` |
| sfx_21 | Relay click | E-stop relay, dock relay | 0,1 s | Klik relay otomotif, logam | `relay click`, `automotive relay` |
| sfx_22 | E-stop press | Scene safety: E-stop ditekan, layar merah | 0,5 s | Klik mushroom button + power-down singkat | `emergency stop button`, `power cut down` |
| sfx_23 | Fault alert | Bay 2 SMART fault (awal simulasi) | 1 s | Alarm pendek dua nada, tidak menakutkan, industrial | `industrial alert beep`, `warning tone short` |
| sfx_24 | Wi-Fi / data link | Garis Modbus dan Wi-Fi beranimasi | 0,5 s | Ping data / chirp digital | `data transmit chirp`, `network ping` |
| sfx_25 | Tag detected / confirm | AprilTag terkunci, ID caddy cocok | 0,3 s | "Lock-on" dua nada naik | `target lock`, `scan confirm beep` |
| sfx_26 | Charging start | Robot docked dan charging di base | 1 s | Bloop listrik naik + hum lembut | `charging start`, `battery charge sound` |
| sfx_27 | Job complete | "Job closed" | 1–1,5 s | Chime positif, hangat, 3 nada | `success chime soft`, `task complete ui` |

### D. Ambience dan manufaktur

| ID | Nama | Dipakai di | Durasi | Karakter | Kata kunci |
|---|---|---|---|---|---|
| sfx_28 | Server room ambience | Bed tipis di scene sistem dan simulasi | loop 10–20 s | Kipas server, airflow rendah, **sangat pelan** | `server room ambience`, `data center hum` |
| sfx_29 | 3D printer | Scene manufaktur (part dicetak) | 2–3 s | Gerakan printer FDM yang "musikal" | `3d printer printing`, `fdm printer` |
| sfx_30 | Packing / zipper | Part masuk ke tas kabin | 1 s | Zipper tas + benda masuk | `bag zipper`, `luggage zip` |
| sfx_31 | Outro hit | Logo akhir 2:26 | 2 s | Versi pendek sfx_01, resolusi akhir | `logo outro hit soft` |

**Total:** 31 SFX (≈ 45 file dengan variasi).

### E. Musik latar

| Hal | Spesifikasi |
|---|---|
| Durasi | ≥ 2:30, atau loop yang bisa disambung dengan bagian intro dan ending yang jelas |
| Tempo | **120 BPM** (cut scene jatuh di bar) |
| Genre | Electronic / tech minimal, cinematic-corporate yang "pintar". Referensi: Apple keynote, Tesla AI Day, Boston Dynamics. Bukan EDM dan bukan corporate ukulele |
| Struktur | Intro tenang (0:00–0:26) → build (0:26–1:20) → energi tertinggi saat simulasi swap (1:48–2:14) → resolusi di penutup |
| Mix | Tanpa vokal, ruang untuk SFX di 2–5 kHz |
| Kata kunci | `technology minimal electronic 120 bpm`, `innovation corporate tech no vocals`, `futuristic pulse cinematic` |
