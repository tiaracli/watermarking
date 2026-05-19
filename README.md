# 🔏 LSB Image Watermarking

Implementasi **invisible watermarking** pada gambar menggunakan algoritma **Least Significant Bit (LSB)** — dibangun dari scratch dengan Python, tanpa library watermarking yang sudah jadi.

Project ini dibuat sebagai bagian dari tugas mata kuliah **Multimedia**, dengan referensi materi dari Modul 15 tentang teknik watermarking pada citra digital.

---

## Apa itu Invisible Watermarking?

Watermarking adalah teknik menyisipkan informasi tersembunyi ke dalam suatu media — dalam kasus ini, gambar. "Invisible" berarti watermark-nya tidak bisa dilihat mata manusia, tapi tetap bisa dibaca secara programatik.

Bedanya dengan watermark biasa (yang teks atau logo-nya kelihatan), invisible watermark bekerja di level bit — mengubah nilai pixel sesedikit mungkin agar perubahan visualnya tidak terdeteksi.

---

## Metode: Least Significant Bit (LSB)

Setiap pixel dalam gambar RGB terdiri dari 3 channel warna: **Red, Green, Blue**. Masing-masing channel direpresentasikan dalam 8 bit (nilai 0–255).

LSB bekerja dengan mengganti **bit terakhir** (bit paling kecil nilainya) dari setiap channel dengan bit dari pesan watermark.

```
Contoh:
Pixel asli  → R: 11001010  (202)
Watermark   → bit: 1
Hasil       → R: 11001011  (203)

Perubahan nilai pixel: hanya 1 angka. Tidak terlihat mata manusia.
```

Karena setiap pixel punya 3 channel, setiap 3 pixel bisa menyimpan 3 bit watermark. Untuk teks 9 karakter (= 72 bit), hanya butuh 24 pixel dari keseluruhan gambar.

---

## Struktur File

```
watermarking/
├── watermark.py          # script untuk menyisipkan watermark
├── baca_watermark.py     # script untuk membaca watermark
├── foto.png              # gambar input (tidak di-push ke repo)
└── foto_watermark.png    # gambar output (tidak di-push ke repo)
```

---

## Requirements

- Python 3.x
- Pillow
- NumPy

Install dependencies:

```bash
pip3 install Pillow numpy
```

---

## Cara Pakai

### 1. Sisipkan Watermark

Edit bagian ini di `watermark.py` sesuai kebutuhan:

```python
sisipkan_watermark(
    nama_foto_asli='foto.png',
    nama_foto_hasil='foto_watermark.png',
    teks_watermark='Tiara2024'   # ganti sesukamu
)
```

Lalu jalankan:

```bash
python3 watermark.py
```

Output:
```
Watermark: 'Tiara2024'
Dalam biner: 01010100011010010110000101110010... (104 bit)

Berhasil! Foto tersimpan sebagai: foto_watermark.png
Total bit yang disisipkan: 104 bit
```

### 2. Baca Watermark

```bash
python3 baca_watermark.py
```

Output:
```
Watermark ditemukan: 'Tiara2024'
```

---

## Cara Kerja Kode

### Menyisipkan (Encode)

```python
def sisipkan_watermark(nama_foto_asli, nama_foto_hasil, teks_watermark):
    # 1. Buka gambar dan konversi ke array pixel
    foto = Image.open(nama_foto_asli).convert('RGB')
    pixels = np.array(foto)

    # 2. Ubah teks watermark ke biner
    teks_dengan_penanda = teks_watermark + '###SELESAI###'
    biner_watermark = teks_ke_biner(teks_dengan_penanda)

    # 3. Sisipkan bit ke LSB setiap channel pixel
    for setiap pixel (i, j) dan channel (k):
        ganti bit terakhir pixel dengan bit watermark

    # 4. Simpan gambar hasil
    Image.fromarray(pixels).save(nama_foto_hasil)
```

### Membaca (Decode)

```python
def baca_watermark(nama_foto):
    # 1. Kumpulkan semua LSB dari tiap pixel
    # 2. Gabungkan jadi string biner
    # 3. Konversi ke teks
    # 4. Cari penanda '###SELESAI###' untuk tahu di mana watermark berakhir
```

---

## Keterbatasan

- Watermark **tidak robust** terhadap kompresi JPG, resize, atau crop — karena LSB bekerja di domain spasial, bukan frekuensi
- Ukuran teks watermark dibatasi oleh ukuran gambar (semakin besar gambar, semakin panjang teks yang bisa disisipkan)
- Menyimpan hasil sebagai `.jpg` akan merusak watermark karena kompresi lossy — gunakan `.png`

---

## Referensi

- Materi Kuliah Multimedia — Modul 15: Watermarking & Encryption
- [ShieldMnt/invisible-watermark](https://github.com/ShieldMnt/invisible-watermark) — referensi struktur project
- [Wikipedia: Least Significant Bit](https://en.wikipedia.org/wiki/Bit_manipulation)