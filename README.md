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

Hill Climbing dengan Sideways Move:

```bash
python -m src.main run <dataset.json> --algorithm hc_sideways --seed <seed> --max-sideways-moves <batas-sideways> --output <folder-output> --plots
```

Hill Climbing dengan Random Restart:

```bash
python -m src.main run <dataset.json> --algorithm hc_random_restart --seed <seed> --max-restarts <batas-restart> --output <folder-output> --plots
```

Stochastic Hill Climbing:

```bash
python -m src.main run <dataset.json> --algorithm hc_stochastic --seed <seed> --max-iterations <batas-iterasi> --output <folder-output> --plots
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
- `<batas-iterasi>`: bilangan bulat positif. Bisa digunakan pada semua HC dan SA; pada Random Restart, batas ini berlaku per percobaan. Stochastic/SA default 1000, HC lain tanpa batas iterasi.
- `<batas-sideways>`: batas perpindahan dengan score sama secara berturut-turut, berupa bilangan bulat nonnegatif (default 100). Hitungan direset saat score meningkat; 0 menonaktifkan sideways.
- `<batas-restart>`: jumlah maksimum pengulangan setelah percobaan awal, berupa bilangan bulat nonnegatif (default 10). Nilai 0 hanya menjalankan percobaan awal; nilai 3 berarti maksimal 4 percobaan.
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

Pada Random Restart, `final.json` dan `best.json` berisi state terbaik dari
seluruh percobaan. Jumlah restart dan iterasi per percobaan tercatat di `run.json`
serta ditampilkan di terminal. Pencarian bisa berhenti lebih awal jika total value
seluruh paket sudah tercapai.

Stochastic memilih satu kandidat acak per iterasi dan hanya menerima perbaikan.
Pencarian berhenti pada batas iterasi; kandidat yang ditolak atau gagal ditemukan
tetap dihitung satu iterasi. Pada Steepest Ascent, Sideways, dan Random Restart,
satu iterasi adalah satu pemeriksaan seluruh neighbor, termasuk pemeriksaan
terakhir tanpa perpindahan.

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
