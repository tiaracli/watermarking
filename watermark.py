from PIL import Image
import numpy as np

def teks_ke_biner(teks):
    """Ubah teks menjadi string biner"""
    hasil = ''
    for karakter in teks:
        hasil += format(ord(karakter), '08b')
    return hasil

def sisipkan_watermark(nama_foto_asli, nama_foto_hasil, teks_watermark):
    """
    Menyisipkan watermark ke dalam foto
    menggunakan metode LSB (Least Significant Bit)
    """
    foto = Image.open(nama_foto_asli)
    foto = foto.convert('RGB')
    pixels = np.array(foto)

    teks_dengan_penanda = teks_watermark + '###SELESAI###'
    biner_watermark = teks_ke_biner(teks_dengan_penanda)

    print(f"Watermark: '{teks_watermark}'")
    print(f"Dalam biner: {biner_watermark[:32]}... ({len(biner_watermark)} bit)")

    total_pixel = pixels.shape[0] * pixels.shape[1] * 3
    if len(biner_watermark) > total_pixel:
        print("ERROR: Foto terlalu kecil atau teks watermark terlalu panjang!")
        return

    index_bit = 0
    for i in range(pixels.shape[0]):          # baris
        for j in range(pixels.shape[1]):      # kolom
            for k in range(3):               # channel R, G, B
                if index_bit < len(biner_watermark):
                    nilai_pixel = pixels[i, j, k]

                    biner_pixel = format(nilai_pixel, '08b')

                    biner_baru = biner_pixel[:7] + biner_watermark[index_bit]

                    pixels[i, j, k] = int(biner_baru, 2)

                    index_bit += 1

    foto_hasil = Image.fromarray(pixels)
    foto_hasil.save(nama_foto_hasil)
    print(f"\nBerhasil! Foto tersimpan sebagai: {nama_foto_hasil}")
    print(f"Total bit yang disisipkan: {index_bit} bit")

sisipkan_watermark(
    nama_foto_asli='foto.jpeg',
    nama_foto_hasil='foto_watermark.png',
    teks_watermark='Tiara18224078'   
)