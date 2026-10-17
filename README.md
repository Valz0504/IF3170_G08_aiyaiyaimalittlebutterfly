# aiyaiyaimalittlebutterfly

## Setup

Gunakan Python **3.11 atau lebih baru**. Jalankan dari root repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Di Windows PowerShell, aktivasi dengan `.venv\Scripts\Activate.ps1`.
Matplotlib disiapkan untuk visualisasi; algoritma akan menggunakan standard
library Python. Fondasi dan tes saat ini dapat dijalankan tanpa menginstal
Matplotlib.

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
