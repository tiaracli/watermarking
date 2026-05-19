from PIL import Image
import numpy as np

def biner_ke_teks(biner):
    """Ubah string biner kembali menjadi teks"""
    teks = ''
    for i in range(0, len(biner), 8):
        delapan_bit = biner[i:i+8]
        if len(delapan_bit) == 8:
            karakter = chr(int(delapan_bit, 2))
            teks += karakter
    return teks

def baca_watermark(nama_foto):
    """
    Membaca watermark yang tersembunyi
    di dalam foto menggunakan metode LSB
    """
    foto = Image.open(nama_foto)
    foto = foto.convert('RGB')
    pixels = np.array(foto)

    semua_bit = ''
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            for k in range(3):
                biner_pixel = format(pixels[i, j, k], '08b')
                semua_bit += biner_pixel[7]  
    teks_hasil = biner_ke_teks(semua_bit)

    penanda = '###SELESAI###'
    if penanda in teks_hasil:
        watermark = teks_hasil[:teks_hasil.index(penanda)]
        print(f"Watermark ditemukan: '{watermark}'")
    else:
        print("Tidak ada watermark ditemukan")

baca_watermark('foto_watermark.png')