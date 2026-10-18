# aiyaiyaimalittlebutterfly

## Setup

Gunakan Python **3.11 atau lebih baru**. Jalankan dari root repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Di Windows PowerShell, aktifkan environment dengan `.venv\Scripts\Activate.ps1`.

## Menjalankan algoritma

Ganti placeholder `<...>` di bawah dengan path atau nilai yang diinginkan, termasuk tanda kurungnya.

- `<dataset.json>`: path file input dengan format seperti `data/example.json`.
- `<folder-output>`: direktori baru untuk menyimpan hasil satu run.
- Gunakan tanda kutip jika path mengandung spasi.

Steepest Ascent Hill Climbing:

```bash
python -m src.main run <dataset.json> --algorithm hc --seed <seed> --output <folder-output> --plots
```

Simulated Annealing:

```bash
python -m src.main run <dataset.json> --algorithm sa --seed <seed> --max-iterations <batas-iterasi> --initial-temperature <suhu-awal> --cooling-rate <faktor-pendinginan> --min-temperature <suhu-minimum> --output <folder-output> --plots
```

Genetic Algorithm:

```bash
python -m src.main run <dataset.json> --algorithm ga --seed <seed> --population-size <jumlah-populasi> --generations <jumlah-generasi> --output <folder-output> --plots
```

Keterangan parameter:

- `<seed>`: bilangan bulat untuk mengatur pengacakan. Initial state dibuat otomatis.
- `<batas-iterasi>`: jumlah iterasi maksimum, berupa bilangan bulat positif. HC juga menerima opsi `--max-iterations <batas-iterasi>`.
- `<suhu-awal>`: suhu awal SA, harus positif.
- `<faktor-pendinginan>`: pengali suhu tiap iterasi SA, harus lebih dari 0 dan kurang dari 1.
- `<suhu-minimum>`: batas suhu SA, harus positif dan lebih kecil dari suhu awal. SA berhenti jika suhu sudah di bawah batas ini.
- `<jumlah-populasi>`: jumlah individu GA, berupa bilangan bulat positif.
- `<jumlah-generasi>`: jumlah generasi GA, berupa bilangan bulat positif.

Gunakan direktori output baru setiap run. Hasil berisi `run.json`, `history.csv`,
`initial.json`, dan `final.json`. Opsi `--plots` menyertakan gambar state dan grafik
history. Gunakan `output/scratch/` untuk percobaan sementara yang diabaikan Git.
Hasil eksperimen final dapat disimpan di luar folder tersebut, misalnya
`output/eksperimen/hc-11/`, agar bisa di-commit. Folder `output/` secara keseluruhan
tidak diabaikan Git.

Pada SA, `final.json` berisi state terakhir dan `best.json` berisi state terbaik
yang ditemukan. Hitungan stuck dimulai dari state setelah langkah pertama.

## Memeriksa dan menampilkan hasil

```bash
python -m src.main validate <snapshot.json>
python -m src.main visualize <snapshot.json>
```

`<snapshot.json>` adalah `initial.json`, `final.json`, atau `best.json` dari folder
hasil, bukan `run.json`. Grafik 3D dapat diputar dengan mouse.
Untuk menyimpan gambar tanpa membuka jendela:

```bash
python -m src.main visualize <snapshot.json> --output <gambar.png>
```

Tambahkan `--show` untuk menyimpan sekaligus menampilkan gambar.

## Membuat initial state saja

```bash
python -m src.main init <dataset.json> --seed <seed> --output <initial.json>
```

Daftar parameter tersedia melalui `python -m src.main run --help`.
