"""
Watermarking Teks — DCT-QIM From Scratch
=========================================
Teknik  : QIM (Quantization Index Modulation) pada domain DCT 8×8
Kanal   : Luminance (Y) dari ruang warna YCbCr
Posisi  : Koefisien mid-frekuensi (u=4, v=1) tiap blok 8×8
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import os

try:
    from PIL import Image
    _PIL = True
except ImportError:
    _PIL = False


EMBED_POS  = (4, 1)          
PENANDA    = '###SELESAI###' 
DELTA_DEF  = 25.0            


_LUMA_Q50 = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68,109,103, 77],
    [24, 35, 55, 64, 81,104,113, 92],
    [49, 64, 78, 87,103,121,120,101],
    [72, 92, 95, 98,112,100,103, 99],
], dtype=np.float64)

_CHROMA_Q50 = np.array([
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
], dtype=np.float64)


def get_quant_table(qf: int, channel: str = 'luma') -> np.ndarray:
    """
    Skala tabel kuantisasi berdasarkan Quality Factor (1–100).

    Rumus (spesifikasi JPEG):
      qf < 50 → scale = 5000 / qf
      qf ≥ 50 → scale = 200 − 2×qf
      table   = floor((base × scale + 50) / 100), clamp [1, 255]
    """
    qf    = int(np.clip(qf, 1, 100))
    scale = 5000.0 / qf if qf < 50 else 200.0 - 2.0 * qf
    base  = _LUMA_Q50 if channel == 'luma' else _CHROMA_Q50
    table = np.floor((base * scale + 50.0) / 100.0)
    return np.clip(table, 1.0, 255.0)


def _build_dct_matrix(N: int = 8) -> np.ndarray:
    """
    Bangun matriks DCT-II ortogonal N×N.

    D[k,n] = sqrt(1/N)                              , k = 0
           = sqrt(2/N) · cos(π·k·(2n+1) / (2N))   , k > 0

    Karena D ortogonal: D⁻¹ = Dᵀ
    """
    D = np.zeros((N, N), dtype=np.float64)
    for k in range(N):
        for n in range(N):
            if k == 0:
                D[k, n] = np.sqrt(1.0 / N)
            else:
                D[k, n] = np.sqrt(2.0 / N) * np.cos(np.pi * k * (2*n + 1) / (2.0 * N))
    return D


_D  = _build_dct_matrix(8)
_DT = _D.T


def dct2(block: np.ndarray) -> np.ndarray:
    """2D DCT-II blok 8×8:  F = D · f · Dᵀ"""
    return _D @ block @ _DT


def idct2(F: np.ndarray) -> np.ndarray:
    """2D IDCT-II blok 8×8:  f = Dᵀ · F · D"""
    return _DT @ F @ _D


# KONVERSI RUANG WARNA

def rgb_to_ycbcr(img: np.ndarray) -> np.ndarray:
    """RGB uint8 [H,W,3] → YCbCr float64 [H,W,3]  (ITU-R BT.601)"""
    R = img[:, :, 0].astype(np.float64)
    G = img[:, :, 1].astype(np.float64)
    B = img[:, :, 2].astype(np.float64)
    Y  =  0.29900*R + 0.58700*G + 0.11400*B
    Cb = -0.16874*R - 0.33126*G + 0.50000*B + 128.0
    Cr =  0.50000*R - 0.41869*G - 0.08131*B + 128.0
    return np.stack([Y, Cb, Cr], axis=2)


def ycbcr_to_rgb(ycbcr: np.ndarray) -> np.ndarray:
    """YCbCr float64 [H,W,3] → RGB uint8 [H,W,3]"""
    Y  = ycbcr[:, :, 0]
    Cb = ycbcr[:, :, 1] - 128.0
    Cr = ycbcr[:, :, 2] - 128.0
    R  = Y + 1.40200 * Cr
    G  = Y - 0.34414 * Cb - 0.71414 * Cr
    B  = Y + 1.77200 * Cb
    return np.clip(np.stack([R, G, B], axis=2), 0, 255).astype(np.uint8)


def jpeg_simulate(img_rgb: np.ndarray, qf: int) -> np.ndarray:
    """
    Simulasi kompresi-dekompresi JPEG dari scratch.

    Pipeline:
      1. RGB → YCbCr
      2. Pad ke kelipatan 8
      3. Batch DCT-II  : F  = D · blok · Dᵀ
      4. Kuantisasi    : Fq = round(F / Q) × Q   ← lossy
      5. Batch IDCT-II : rekon = Dᵀ · Fq · D
      6. Crop padding, clip [0, 255]
      7. YCbCr → RGB
    """
    ycbcr  = rgb_to_ycbcr(img_rgb)
    H, W   = ycbcr.shape[:2]
    pH     = H + (-H % 8)
    pW     = W + (-W % 8)
    nh, nw = pH // 8, pW // 8
    out    = np.zeros((H, W, 3), dtype=np.float64)

    for c in range(3):
        qtable = get_quant_table(qf, 'luma' if c == 0 else 'chroma')
        ch     = ycbcr[:, :, c]
        padded = np.pad(ch, ((0, pH - H), (0, pW - W)), mode='edge') - 128.0
        blocks = padded.reshape(nh, 8, nw, 8).transpose(0, 2, 1, 3)
        F      = _D @ blocks @ _DT
        Fq     = np.round(F / qtable) * qtable
        rekon  = _DT @ Fq @ _D
        recon  = rekon.transpose(0, 2, 1, 3).reshape(pH, pW)
        out[:, :, c] = np.clip(recon[:H, :W] + 128.0, 0.0, 255.0)

    return ycbcr_to_rgb(out)


# KONVERSI TEKS ↔ BINER

def teks_ke_biner(teks: str) -> str:
    """Ubah teks menjadi string biner (8 bit per karakter)."""
    return ''.join(format(ord(c), '08b') for c in teks)


def biner_ke_teks(biner: str) -> str:
    """Ubah string biner kembali menjadi teks."""
    teks = ''
    for i in range(0, len(biner) - 7, 8):
        teks += chr(int(biner[i:i+8], 2))
    return teks


# QIM — QUANTIZATION INDEX MODULATION

def _embed_bit_qim(coeff: float, bit: int, delta: float) -> float:
    """
    Sisipkan 1 bit ke dalam koefisien DCT menggunakan QIM.

    Kuantizer ganda:
      bit 0 → nearest even  multiple of delta: 2 × round(coeff / 2δ) × δ
      bit 1 → nearest odd   multiple of delta: (2 × round((coeff − δ) / 2δ) + 1) × δ

    Maksimum distorsi = δ/2  (terkontrol, tidak bergantung nilai koefisien).
    """
    if bit == 0:
        q = int(round(coeff / (2.0 * delta)))
        return float(2.0 * q * delta)
    else:
        q = int(round((coeff - delta) / (2.0 * delta)))
        return float((2.0 * q + 1) * delta)


def _extract_bit_qim(coeff: float, delta: float) -> int:
    """
    Ekstrak 1 bit dari koefisien DCT (semi-blind — tidak butuh gambar asli).

    bit = round(coeff / delta) mod 2
    Python % selalu menghasilkan 0 atau 1 untuk operand positif maupun negatif.
    """
    return int(round(coeff / delta)) % 2



def sisipkan_watermark(
    nama_foto_asli: str,
    nama_foto_hasil: str,
    teks_watermark: str,
    delta: float = DELTA_DEF
) -> np.ndarray:
    """
    Sisipkan watermark teks ke foto menggunakan DCT-QIM.

    Pipeline:
      1. Baca foto → RGB
      2. RGB → YCbCr
      3. Pad kanal Y ke kelipatan 8
      4. Tiap blok 8×8 → DCT → modifikasi koefisien EMBED_POS dengan QIM
      5. IDCT → rekonstruksi kanal Y
      6. YCbCr → RGB → simpan sebagai PNG (lossless)

    Returns: numpy uint8 [H,W,3] foto yang sudah disisipkan watermark.
    """
    if not (_PIL and os.path.exists(nama_foto_asli)):
        raise FileNotFoundError(f"File '{nama_foto_asli}' tidak ditemukan.")

    img  = np.array(Image.open(nama_foto_asli).convert('RGB'))
    H, W = img.shape[:2]

    # --- Persiapan bit payload ---
    payload  = teks_watermark + PENANDA
    bits     = teks_ke_biner(payload)
    n_bits   = len(bits)
    n_blocks = (H // 8) * (W // 8)

    print(f"Watermark     : '{teks_watermark}'")
    print(f"Payload       : {n_bits} bit  ({len(payload)} karakter)")
    print(f"Kapasitas foto: {n_blocks} blok 8×8 tersedia")

    if n_bits > n_blocks:
        raise ValueError(
            f"Teks terlalu panjang! Butuh {n_bits} blok, tersedia {n_blocks}."
        )

    ycbcr = rgb_to_ycbcr(img).copy()
    Y     = ycbcr[:, :, 0].copy()
    pH    = H + (-H % 8)
    pW    = W + (-W % 8)
    Ypad  = np.pad(Y, ((0, pH - H), (0, pW - W)), mode='edge') - 128.0

    nh, nw = pH // 8, pW // 8
    u, v   = EMBED_POS

    bit_idx = 0
    for bi in range(nh):
        for bj in range(nw):
            if bit_idx >= n_bits:
                break
            block       = Ypad[bi*8:(bi+1)*8, bj*8:(bj+1)*8].copy()
            F           = dct2(block)
            F[u, v]     = _embed_bit_qim(F[u, v], int(bits[bit_idx]), delta)
            Ypad[bi*8:(bi+1)*8, bj*8:(bj+1)*8] = idct2(F)
            bit_idx    += 1
        if bit_idx >= n_bits:
            break

    ycbcr[:, :, 0] = np.clip(Ypad[:H, :W] + 128.0, 0.0, 255.0)
    result = ycbcr_to_rgb(ycbcr)

    Image.fromarray(result).save(nama_foto_hasil)
    print(f"\nBerhasil! Foto tersimpan sebagai '{nama_foto_hasil}'")
    print(f"Bit tersisip  : {bit_idx} bit pada {bit_idx} blok pertama dari {n_blocks} blok")
    return result


def baca_watermark(
    nama_foto: str,
    delta: float = DELTA_DEF,
    max_chars: int = 500
) -> str:
    """
    Baca watermark yang tersembunyi dalam foto (semi-blind — tidak butuh foto asli).

    Pipeline:
      1. Buka foto → RGB → YCbCr
      2. Pad kanal Y ke kelipatan 8
      3. Tiap blok 8×8 → DCT 2D
      4. Baca koefisien EMBED_POS, hitung bit via QIM
      5. Kumpulkan bit → konversi ke teks → cari penanda '###SELESAI###'
    """
    if not (_PIL and os.path.exists(nama_foto)):
        raise FileNotFoundError(f"File '{nama_foto}' tidak ditemukan.")

    img  = np.array(Image.open(nama_foto).convert('RGB'))
    H, W = img.shape[:2]

    ycbcr    = rgb_to_ycbcr(img)
    Y        = ycbcr[:, :, 0]
    pH       = H + (-H % 8)
    pW       = W + (-W % 8)
    Ypad     = np.pad(Y, ((0, pH - H), (0, pW - W)), mode='edge') - 128.0

    nh, nw   = pH // 8, pW // 8
    u, v     = EMBED_POS
    max_bits = min(max_chars * 8 * 10, nh * nw)

    bits_list = []
    for bi in range(nh):
        for bj in range(nw):
            if len(bits_list) >= max_bits:
                break
            block = Ypad[bi*8:(bi+1)*8, bj*8:(bj+1)*8]
            F     = dct2(block)
            bits_list.append(str(_extract_bit_qim(F[u, v], delta)))
        if len(bits_list) >= max_bits:
            break

    raw = biner_ke_teks(''.join(bits_list))

    print(f"Foto   : {nama_foto}  ({W}×{H} px)")
    print(f"Metode : DCT-QIM  |  delta={delta}  |  posisi koef={EMBED_POS}")
    print("-" * 55)

    if PENANDA in raw:
        watermark = raw[:raw.index(PENANDA)]
        print(f"Watermark ditemukan : '{watermark}'")
        return watermark
    else:
        print("Watermark TIDAK ditemukan  (penanda akhir tidak terdeteksi).")
        print(f"  Cuplikan teks : {raw[:60]!r}")
        print()
        print("  Kemungkinan penyebab:")
        print("  • Foto dikompresi JPEG setelah penyisipan (gunakan PNG/BMP)")
        print("  • Nilai delta berbeda dengan saat penyisipan")
        print("  • Foto bukan hasil sisipkan_watermark() ini")
        return ''


def psnr(ref: np.ndarray, test: np.ndarray) -> float:
    """PSNR (Peak Signal-to-Noise Ratio) dalam dB."""
    mse = np.mean((ref.astype(np.float64) - test.astype(np.float64)) ** 2)
    return float('inf') if mse == 0 else 10.0 * np.log10(255.0**2 / mse)


def bit_accuracy(teks_asli: str, teks_ekstrak: str) -> float:
    """Akurasi bit antara watermark asli dan hasil ekstraksi (0.0–1.0)."""
    b1 = teks_ke_biner(teks_asli + PENANDA)
    te = teks_ekstrak[:len(teks_asli)] if len(teks_ekstrak) >= len(teks_asli) \
         else teks_ekstrak.ljust(len(teks_asli))
    b2 = teks_ke_biner(te + PENANDA)
    n  = min(len(b1), len(b2))
    return sum(c1 == c2 for c1, c2 in zip(b1[:n], b2[:n])) / n if n else 0.0


def normalized_correlation(teks_asli: str, teks_ekstrak: str) -> float:
    """NC antara vektor bit watermark asli dan ekstraksi (dipetakan ke {-1,+1})."""
    te  = teks_ekstrak[:len(teks_asli)].ljust(len(teks_asli))
    b1  = np.array([int(b)*2-1 for b in teks_ke_biner(teks_asli)], dtype=np.float64)
    b2  = np.array([int(b)*2-1 for b in teks_ke_biner(te)],        dtype=np.float64)
    den = np.linalg.norm(b1) * np.linalg.norm(b2)
    return float(np.dot(b1, b2) / den) if den > 1e-12 else 0.0


def evaluasi(
    nama_foto_asli: str,
    nama_foto_watermark: str,
    teks_watermark: str,
    delta: float = DELTA_DEF,
    qfs: list = None
) -> None:
    """
    Evaluasi ketahanan watermark terhadap kompresi JPEG di berbagai Quality Factor.
    Mencetak tabel akurasi bit & NC, lalu menampilkan visualisasi lengkap.
    """
    if qfs is None:
        qfs = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]

    ACC_THRESH = 0.90
    TMP        = '_tmp_eval.png'

    original = np.array(Image.open(nama_foto_asli).convert('RGB'))
    marked   = np.array(Image.open(nama_foto_watermark).convert('RGB'))

    print(f"\nPSNR watermarked : {psnr(original, marked):.2f} dB")
    print(f"\n{'QF':>5}  {'Akurasi Bit':>12}  {'NC':>8}  {'PSNR (dB)':>10}  Status")
    print("-" * 62)

    acc_vals   = []
    nc_vals    = []
    psnr_vals  = []
    compressed = {}

    for qf in qfs:
        comp = jpeg_simulate(marked, qf)
        Image.fromarray(comp).save(TMP)
        wm_ex = baca_watermark(TMP, delta=delta, max_chars=500)

        acc = bit_accuracy(teks_watermark, wm_ex)
        nc  = normalized_correlation(teks_watermark, wm_ex)
        p   = psnr(original, comp)

        acc_vals.append(acc)
        nc_vals.append(nc)
        psnr_vals.append(p)
        compressed[qf] = comp

        status  = "OK  (terekstrak)" if acc >= ACC_THRESH else "HILANG"
        wm_show = f"'{wm_ex}'" if len(wm_ex) <= 15 else f"'{wm_ex[:12]}...'"
        print(f"{qf:>5}  {acc*100:>11.1f}%  {nc:>8.4f}  {p:>10.2f}  {status}  {wm_show}")

    if os.path.exists(TMP):
        os.remove(TMP)

    first_lost = next((qf for qf, a in zip(qfs, acc_vals) if a < ACC_THRESH), None)
    print()
    if first_lost:
        print(f"=> Watermark rusak pada QF <= {first_lost}  (akurasi bit < {ACC_THRESH*100:.0f}%)")
    else:
        print("=> Watermark tetap terekstrak pada semua QF yang diuji.")

    # ---- Visualisasi ----
    SHOWCASE = [qfs[0], qfs[3], qfs[6], qfs[-1]]   # 4 titik representatif

    fig = plt.figure(figsize=(20, 13))
    fig.suptitle(
        f'Evaluasi Watermarking DCT-QIM — From Scratch\n'
        f'(teks="{teks_watermark}",  δ={delta},  posisi DCT={EMBED_POS})',
        fontsize=13, fontweight='bold'
    )

    # Baris 1 — foto asli, watermarked, selisih, info
    ax = fig.add_subplot(3, 4, 1)
    ax.imshow(original); ax.set_title('Foto Asli'); ax.axis('off')

    ax = fig.add_subplot(3, 4, 2)
    ax.imshow(marked); ax.set_title(f'Watermarked  (δ={delta})'); ax.axis('off')

    diff = np.clip(
        (marked.astype(np.int32) - original.astype(np.int32)) * 10 + 128, 0, 255
    ).astype(np.uint8)
    ax = fig.add_subplot(3, 4, 3)
    ax.imshow(diff); ax.set_title('Selisih ×10  (visibilitas)'); ax.axis('off')

    ax = fig.add_subplot(3, 4, 4)
    ax.axis('off')
    info = (
        f"Teks     : {teks_watermark}\n"
        f"Payload  : {len(teks_watermark + PENANDA)} karakter\n"
        f"         : {len(teks_ke_biner(teks_watermark + PENANDA))} bit\n"
        f"Metode   : DCT-QIM\n"
        f"Posisi   : koef {EMBED_POS}\n"
        f"Delta    : {delta}\n"
        f"PSNR     : {psnr(original, marked):.2f} dB"
    )
    ax.text(0.05, 0.95, info, transform=ax.transAxes, fontsize=9.5,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#fffde7', alpha=0.9))
    ax.set_title('Info Embedding')

    # Baris 2 — foto setelah kompresi JPEG
    for k, qf in enumerate(SHOWCASE):
        ax  = fig.add_subplot(3, 4, 5 + k)
        ax.imshow(compressed[qf])
        acc_v = acc_vals[qfs.index(qf)]
        nc_v  = nc_vals[qfs.index(qf)]
        sym   = '✓' if acc_v >= ACC_THRESH else '✗'
        ax.set_title(f'JPEG QF={qf}  {sym}\nAcc={acc_v*100:.0f}%   NC={nc_v:.3f}')
        ax.axis('off')

    # Baris 3 — teks terekstrak per QF
    TMP2 = '_tmp_vis.png'
    for k, qf in enumerate(SHOWCASE[:3]):
        Image.fromarray(compressed[qf]).save(TMP2)
        wm_v = baca_watermark(TMP2, delta=delta, max_chars=500)

        ax = fig.add_subplot(3, 4, 9 + k)
        ax.axis('off')
        warna = 'green' if wm_v == teks_watermark else 'red'
        ax.text(0.5, 0.60, f'"{wm_v}"',
                ha='center', va='center',
                fontsize=10, fontfamily='monospace', color=warna)
        ax.text(0.5, 0.25, f'QF = {qf}',
                ha='center', va='center', fontsize=9, color='gray')
        ax.set_title(f'Ekstrak WM  (QF={qf})')
        rect = plt.Rectangle((0.02, 0.02), 0.96, 0.96,
                              fill=False, edgecolor=warna,
                              linewidth=2, transform=ax.transAxes)
        ax.add_patch(rect)

    if os.path.exists(TMP2):
        os.remove(TMP2)

    # Plot Akurasi Bit & NC vs QF
    ax  = fig.add_subplot(3, 4, 12)
    ax2 = ax.twinx()
    lns1 = ax.plot(qfs, [a * 100 for a in acc_vals],
                   'b-o', linewidth=2.5, markersize=8, label='Akurasi Bit (%)')
    lns2 = ax2.plot(qfs, nc_vals,
                    'g-s', linewidth=2, markersize=6, label='NC', alpha=0.75)
    ax.axhline(ACC_THRESH * 100, color='red', linestyle='--',
               linewidth=1.8, label=f'Threshold {ACC_THRESH*100:.0f}%')
    if first_lost:
        ax.axvline(first_lost, color='orange', linestyle=':',
                   linewidth=2, label=f'Hilang QF={first_lost}')

    ax.set_xlabel('Quality Factor (QF)')
    ax.set_ylabel('Akurasi Bit (%)', color='blue')
    ax2.set_ylabel('Normalized Correlation', color='green')
    ax.set_title('Ketahanan Watermark vs Kompresi JPEG')
    ax.invert_xaxis()
    ax.set_ylim(-5, 110)
    ax2.set_ylim(-0.1, 1.1)
    ax.set_xlim(max(qfs) + 5, min(qfs) - 5)
    ax.grid(True, alpha=0.3)
    lns  = lns1 + lns2
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, fontsize=7, loc='lower right')

    plt.tight_layout()
    out_file = 'watermark_evaluation.png'
    plt.savefig(out_file, dpi=130, bbox_inches='tight')
    print(f"\nVisualisasi disimpan ke '{out_file}'")
    plt.show()


if __name__ == '__main__':

    args = sys.argv[1:]

    if args and args[0] == 'sisip':
        # --- Mode: sisipkan watermark ---
        if len(args) < 4:
            print("Penggunaan: python watermark.py sisip <foto_asli> <foto_hasil> <teks>")
            sys.exit(1)
        sisipkan_watermark(args[1], args[2], args[3])

    elif args and args[0] == 'baca':
        # --- Mode: baca watermark ---
        if len(args) < 2:
            print("Penggunaan: python watermark.py baca <foto_watermark>")
            sys.exit(1)
        baca_watermark(args[1])

    elif args and args[0] == 'evaluasi':
        # --- Mode: evaluasi ketahanan ---
        if len(args) < 4:
            print("Penggunaan: python watermark.py evaluasi <foto_asli> <foto_watermark> <teks>")
            sys.exit(1)
        evaluasi(args[1], args[2], args[3])

    else:
        # --- Demo lengkap (tanpa argumen) ---
        FOTO_ASLI  = 'fotoo.jpeg'
        FOTO_HASIL = 'foto_watermark.png'
        TEKS_WM    = 'Tiara18224078'

        print("=" * 65)
        print("  Watermarking DCT-QIM — From Scratch")
        print("=" * 65)

        # 1. Sisipkan
        print("\n[ SISIPKAN WATERMARK ]")
        marked = sisipkan_watermark(FOTO_ASLI, FOTO_HASIL, TEKS_WM)

        # 2. Baca kembali
        print("\n[ BACA WATERMARK ]")
        baca_watermark(FOTO_HASIL)

        # 3. Evaluasi ketahanan vs JPEG
        print("\n[ EVALUASI KETAHANAN VS JPEG ]")
        evaluasi(FOTO_ASLI, FOTO_HASIL, TEKS_WM)