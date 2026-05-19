# LSB Image Watermarking

Implementasi **invisible watermarking** pada gambar menggunakan algoritma **Least Significant Bit (LSB)** menggunakan Python, tanpa library watermarking.

Project ini dibuat sebagai tugas mata kuliah **Sistem Multimedia**, dengan referensi materi teknik watermarking pada citra digital.

---

## Apa itu Invisible Watermarking?

Watermarking adalah teknik menyisipkan informasi tersembunyi ke dalam suatu media. "Invisible" berarti watermark-nya tidak bisa dilihat mata manusia, tapi tetap bisa dibaca secara programatik.

Bedanya dengan watermark biasa (yang teks atau logonya kelihatan), invisible watermark bekerja di level bit yang mengubah nilai pixel sesedikit mungkin agar perubahan visualnya tidak terdeteksi.

---

## Metode: Least Significant Bit (LSB)

Setiap pixel dalam gambar RGB terdiri dari 3 channel warna yaitu **Red, Green, Blue**. Masing-masing channel direpresentasikan dalam 8 bit (nilai 0–255).

LSB bekerja dengan mengganti bit terakhir (bit paling kecil nilainya) dari setiap channel dengan bit dari pesan watermark.

```
Contoh:
Pixel asli   R: 11001010  (202)
Watermark    bit: 1
Hasil        R: 11001011  (203)

Perubahan nilai pixel hanya 1 angka. Tidak terlihat mata manusia.
```

Karena setiap pixel punya 3 channel, setiap 3 pixel bisa menyimpan 3 bit watermark. Untuk teks 9 karakter (72 bit), hanya butuh 24 pixel dari keseluruhan gambar.

---

## Struktur File

```
watermarking/
├── watermark.py          # script untuk menyisipkan watermark
├── baca_watermark.py     # script untuk membaca watermark
├── foto.png              # gambar input 
└── foto_watermark.png    # gambar output 
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

### 1. Menyisipkan Watermark

```python
sisipkan_watermark(
    nama_foto_asli='foto.jpeg',
    nama_foto_hasil='foto_watermark.png',
    teks_watermark='Tiara18224078'   
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

### 2. Membaca Watermark

```bash
python3 baca_watermark.py
```

Output:
```
Watermark ditemukan: 'Tiara18224078'
```

---

## Cara Kerja Kode

### Menyisipkan (Encode)

```python
def sisipkan_watermark(nama_foto_asli, nama_foto_hasil, teks_watermark):
    # Buka gambar dan konversi ke array pixel
    foto = Image.open(nama_foto_asli).convert('RGB')
    pixels = np.array(foto)

    # Ubah teks watermark ke biner
    teks_dengan_penanda = teks_watermark + '###SELESAI###'
    biner_watermark = teks_ke_biner(teks_dengan_penanda)

    # Sisipkan bit ke LSB setiap channel pixel
    for setiap pixel (i, j) dan channel (k):
        ganti bit terakhir pixel dengan bit watermark

    # Simpan gambar hasil
    Image.fromarray(pixels).save(nama_foto_hasil)
```

### Membaca (Decode)

```python
def baca_watermark(nama_foto):
    # Kumpulkan semua LSB dari tiap pixel
    # Gabungkan jadi string biner
    # Konversi ke teks
    # Cari penanda '###SELESAI###' untuk tahu di mana watermark berakhir
```

---

## Keterbatasan

- Watermark tidak robust terhadap kompresi JPG, resize, atau crop karena LSB bekerja di domain spasial, bukan frekuensi
- Ukuran teks watermark dibatasi oleh ukuran gambar (semakin besar gambar, semakin panjang teks yang bisa disisipkan)
- Menyimpan hasilnya sebagai `.jpg` akan merusak watermark karena kompresi lossy, jadi digunakan `.png`

---

## Referensi

- Materi Kuliah Sistem Multimedia Modul 15: Realitas Virtual & Digital Rights Management
- [Wikipedia: Least Significant Bit](https://en.wikipedia.org/wiki/Bit_manipulation)
