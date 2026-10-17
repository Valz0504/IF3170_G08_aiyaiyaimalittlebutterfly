# aiyaiyaimalittlebutterfly

## Setup

Gunakan Python **3.11 atau lebih baru**. Jalankan dari root repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Di Windows PowerShell, aktivasi dengan `.venv\Scripts\Activate.ps1`.
Matplotlib digunakan untuk visualisasi. Perintah `init`, `validate`, `run` tanpa
`--plots`, serta tes HC dapat dijalankan tanpa Matplotlib. Untuk visualisasi,
instal dependency di `requirements.txt`.

## Menjalankan proyek

Jalankan dari root repository untuk membuat initial state acak:

```bash
python -m src.main init data/example.json --seed 11
```

Program menampilkan validitas state, jumlah paket di dalam/luar, berat, dan score.
Untuk menyimpan serta memeriksa ulang state:

```bash
python -m src.main init data/example.json --seed 11 --output output/scratch/initial-11.json
python -m src.main validate output/scratch/initial-11.json
```

Gunakan nama output baru untuk run berikutnya; file lama tidak ditimpa. Folder
`output/scratch/` diabaikan Git. Snapshot berisi seluruh input dan placement,
termasuk paket luar. Perintah ini membuat initial state, belum menjalankan optimasi.
Daftar perintah tersedia melalui `python -m src.main --help`.

## Menampilkan visualisasi

Buka snapshot yang sudah dibuat dalam jendela Matplotlib. Grafik 3D dapat diputar
dengan mouse:

```bash
python -m src.main visualize output/scratch/initial-11.json --title "Initial state"
```

Simpan gambar tanpa membuka jendela:

```bash
python -m src.main visualize output/scratch/initial-11.json --output output/scratch/initial-11.png --title "Initial state"
```

Tambahkan `--show` untuk menyimpan sekaligus membuka jendela. Gunakan nama gambar
baru jika file sudah ada. Gambar menampilkan paket dalam/luar truk, orientasi,
penanda fragile, score, dan berat muatan. Snapshot state akhir nantinya dapat
ditampilkan dengan perintah yang sama.

Perintah ini hanya untuk satu run. Runner eksperimen berulang belum dibuat.

## Pengujian Hill Climbing

File tes berada di `src/test_hill_climbing.py`. Jalankan dari root repository:

```bash
python -m unittest src.test_hill_climbing -v
```
