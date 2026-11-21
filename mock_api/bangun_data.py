"""
Generator data SINTETIS penuh untuk instance API tiruan grup Angkasa Biru: tiga HRIS perusahaan
(Angkasa Biru, Angkasa Biru Retail, Angkasa Biru Destination) dan dua sistem grup (LMS, TMS).

Sejak 15 November 2026 (keputusan penghapusan data asli): TIDAK ADA satu pun data pegawai sungguhan.
Seluruh nama, NIK, tanggal, dan nilai dibangkitkan deterministik (seed tetap), sehingga:
  - dua kali start menghasilkan data yang persis sama (registry id_employee stabil antar-run);
  - bentuk payload (nama kunci, format nilai, keanehan API asli seperti kolom `id_emloyee`,
    `home_phone` berisi ponsel, NIP berawalan nol, kode varian 'PM_') dipertahankan agar
    staging dbt dan uji pytest tetap berlaku.

Dipakai oleh:
  mock_api/app.py                     : dataset per endpoint, dibangun saat start.
  python mock_api/bangun_data.py \
      --sample DIR --referensi DIR    : menulis fixture mode sample dan CSV referensi sintetis.
"""
import argparse
import json
import random
import zlib
from datetime import date, timedelta
from pathlib import Path

# --------------------------------------------------------------------- kosakata
DEPAN = ["Adi", "Budi", "Citra", "Dewi", "Eko", "Fajar", "Gita", "Hendra", "Indah", "Joko",
         "Kartika", "Lestari", "Maya", "Nanda", "Oka", "Putri", "Rizki", "Sari", "Tono", "Utami",
         "Vina", "Wawan", "Yulia", "Zaki", "Agus", "Bayu", "Dian", "Fitri", "Galih", "Hana"]
BELAKANG = ["Pratama", "Santoso", "Wijaya", "Saputra", "Kusuma", "Hidayat", "Nugroho", "Rahayu",
            "Setiawan", "Permata", "Siregar", "Nasution", "Wibowo", "Hartono", "Gunawan", "Susanti",
            "Firmansyah", "Maulana", "Puspita", "Ramadhan", "Halim", "Suryadi", "Anggraini", "Yusuf"]
KOTA_PROVINSI = [("Jakarta", "DKI Jakarta"), ("Surabaya", "Jawa Timur"), ("Medan", "Sumatera Utara"),
                 ("Makassar", "Sulawesi Selatan"), ("Denpasar", "Bali"), ("Yogyakarta", "DI Yogyakarta"),
                 ("Semarang", "Jawa Tengah"), ("Palembang", "Sumatera Selatan"),
                 ("Balikpapan", "Kalimantan Timur"), ("Manado", "Sulawesi Utara"),
                 ("Padang", "Sumatera Barat"), ("Bandung", "Jawa Barat")]
KOTA = [k for k, _ in KOTA_PROVINSI]
PROVINSI = dict(KOTA_PROVINSI)   # alamat selalu memakai pasangan kota-provinsi yang benar
GELAR = [None, None, None, "S.T.", "S.E.", "S.Kom.", "S.H.", "M.M.", "M.T.", "A.Md."]
UNIVERSITAS = ["Universitas Indonesia", "Institut Teknologi Bandung", "Universitas Gadjah Mada",
               "Universitas Airlangga", "Universitas Hasanuddin", "Politeknik Negeri Jakarta",
               "Universitas Trisakti", "Universitas Brawijaya"]
JURUSAN = ["Teknik Industri", "Manajemen", "Akuntansi", "Teknik Informatika", "Ilmu Hukum",
           "Teknik Sipil", "Administrasi Bisnis", "Psikologi", "Teknik Elektro", "Statistika"]
PERIODE = ["2025-S2", "2026-S1"]
METODE_ASES = ["Assessment Center", "360 Feedback", "Online Assessment"]
PENYEDIA = ["Angkasa Biru Corporate University", "LMS Angkasa Biru", "Prasetiya Mulya", "PPM Manajemen", "Internal"]
PELATIHAN_WAJIB = [("Pelatihan Penjenjangan Dasar", "Penjenjangan"),
                   ("Pelatihan Penjenjangan Lanjutan", "Penjenjangan")]
PELATIHAN_UMUM = [("Service Excellence", "Teknis"), ("Keselamatan Kerja (K3)", "Teknis"),
                  ("Digital Mindset", "Teknis"), ("Leadership Fundamental", "Kepemimpinan"),
                  ("Manajemen Risiko", "Teknis"), ("Bahasa Inggris Bisnis", "Teknis"),
                  ("Sertifikasi Profesi", "Sertifikasi"), ("Budaya AKHLAK", "Kepemimpinan")]
# (nama mentah Angkasa Biru Retail, kategori: 1 Core / 2 Leadership / 3 Functional) -> nama baku di seed map_nilai_angkasabiruretail
KOMPETENSI = [("Conceptual Thinking - CTH", "1"), ("Agility & Adaptability - AAD", "1"),
              ("Intitiative - INI", "1"), ("Attention to Detail - ATD", "1"),
              ("Customer Focus - CFO", "1"), ("Concern for Order and Accuracy - COA", "1"),
              ("Leading Change - LCH", "2"), ("Impact Through Influence - ITI", "2"),
              ("Managing Diversity - MDI", "2"), ("Developing Organizational Capabilities - DOC", "2"),
              ("Strategic Orientation - SOR", "2"), ("Digital Leadership - DLE", "2"),
              ("Global Business Savvy - GBS", "3"), ("Optimizing Work Process - OWP", "3"),
              ("Driving Execution - DEX", "3"), ("Building Strategic Partnership - BSP", "3"),
              ("Business Perspective - BPR", "3"), ("Driving Innovation - DIN", "3")]
KATEGORI_KOMPETENSI = {"1": "Core Competency", "2": "Leadership Competency", "3": "Functional Competency"}
# bentuk baku tiap kompetensi (hasil seed map_nilai_angkasabiruretail); dipakai langsung oleh data AP
KOMPETENSI_BAKU = {"Conceptual Thinking - CTH": "Conceptual Thinking", "Agility & Adaptability - AAD": "Agility & Adaptability",
                   "Intitiative - INI": "Initiative", "Attention to Detail - ATD": "Attention to Detail",
                   "Customer Focus - CFO": "Customer Focus Orientation",
                   "Concern for Order and Accuracy - COA": "Concern for Order & Accuracy",
                   "Leading Change - LCH": "Leading Change", "Impact Through Influence - ITI": "Impact Through Influence",
                   "Managing Diversity - MDI": "Managing Diversity",
                   "Developing Organizational Capabilities - DOC": "Developing Organization Capabilities",
                   "Strategic Orientation - SOR": "Strategic Orientation", "Digital Leadership - DLE": "Digital Leadership",
                   "Global Business Savvy - GBS": "Global Business Savvy", "Optimizing Work Process - OWP": "Optimizing Work Process",
                   "Driving Execution - DEX": "Driving Execution", "Building Strategic Partnership - BSP": "Building Strategic Partnership",
                   "Business Perspective - BPR": "Business Perspective", "Driving Innovation - DIN": "Driving Innovation"}
FUNGSI_POSISI = ["Manager", "Officer", "Analyst", "Supervisor", "Specialist", "Staff", "Team Leader", "Inspector"]
BIDANG = ["Operasional", "Keuangan", "Human Capital", "Komersial", "Teknik", "Teknologi Informasi",
          "Pengadaan", "Hukum", "Keselamatan", "Pelayanan Pelanggan", "Kargo", "Perencanaan"]


def _rng(*kunci) -> random.Random:
    return random.Random(zlib.crc32("|".join(str(k) for k in kunci).encode()))


def _tanggal(r, awal: date, akhir: date) -> date:
    return awal + timedelta(days=r.randrange((akhir - awal).days + 1))


def _nama(r) -> str:
    return f"{r.choice(DEPAN)} {r.choice(DEPAN)} {r.choice(BELAKANG)}" if r.random() < 0.4 \
        else f"{r.choice(DEPAN)} {r.choice(BELAKANG)}"


def _email(nama, domain, r) -> str:
    inti = ".".join(nama.lower().split()[:2])
    return f"{inti}{r.randrange(10, 99)}@{domain}"


def _ponsel(r) -> str:
    return "08" + "".join(str(r.randrange(10)) for _ in range(r.choice([9, 10])))


def _digit(r, n) -> str:
    return "".join(str(r.randrange(10)) for _ in range(n))


def _pensiun(lahir, usia):
    """Tanggal pensiun = ulang tahun ke-<usia> (AB 58, ABR 56)."""
    return date(lahir.year + usia, lahir.month, min(lahir.day, 28))


def _agility(nik):
    r = _rng("agility", nik)
    baris = []
    for periode in PERIODE:
        if periode == PERIODE[0] and r.random() < 0.15:
            continue
        sub = {k: round(r.uniform(55, 95), 1)
               for k in ("mental_agility", "people_agility", "change_agility", "results_agility")}
        baris.append({"id_employee": nik, "assessment_period": periode,
                      "learning_agility_score": round(sum(sub.values()) / 4, 1), **sub,
                      "dt_assessment": _tanggal(r, date(2025, 7, 1) if periode == PERIODE[0] else date(2026, 1, 1),
                                                date(2025, 12, 20) if periode == PERIODE[0] else date(2026, 6, 30)).isoformat()})
    return baris


# --------------------------------------------------------------------- Talent Mobility (20 Nov 2026)
# Sebagian kecil pegawai PKWTT diperbantukan antar perusahaan grup. Orangnya SAMA di dua perusahaan
# (nama, tanggal lahir, jenis kelamin, KTP, NPWP): di perusahaan ASAL berstatus diperbantukan
# (non-aktif; tinggal record history, riwayat posisinya ditutup pada tanggal pindah), di perusahaan
# TUJUAN aktif dengan kontrak PKWTT. employment_type di tujuan: 'Talent Mobility' pada ABR dan ABD,
# 'PKWTT' pada AB (API-nya hanya mengenal PKWTT dan PKWT); karena itu gold mengenali mereka dari
# id_nik yang sama di dua perusahaan, bukan dari employment_type. Karena gold menyaring
# employment_status = 'aktif', nama mereka hanya muncul sekali di gold: di perusahaan terakhir.
MOBILITAS = [("AB", "ABR", 3), ("AB", "ABD", 3), ("ABR", "ABD", 2),
             ("ABR", "AB", 2), ("ABD", "AB", 1), ("ABD", "ABR", 1)]


def _daftar_mobilitas():
    """Daftar deterministik orang Talent Mobility; dipanggil ketiga builder dengan hasil identik."""
    orang, k = [], 0
    for asal, tujuan, n in MOBILITAS:
        for _ in range(n):
            r = _rng("mobilitas", k)
            # lahir 1975-1995: belum melewati usia pensiun termuda (56) di perusahaan mana pun
            lahir = _tanggal(r, date(1975, 1, 1), date(1995, 12, 28))
            tmt_asal = _tanggal(r, date(max(2005, lahir.year + 18), 1, 1), date(2020, 12, 28))
            tmt_pindah = _tanggal(r, date(2024, 1, 1), date(2026, 6, 30))
            orang.append({"k": k, "asal": asal, "tujuan": tujuan, "nama": _nama(r),
                          "gender": r.choice(["L", "P"]), "lahir": lahir, "kota": r.choice(KOTA),
                          "id_nik": _digit(r, 16),
                          "id_npwp": f"{_digit(r, 2)}.{_digit(r, 3)}.{_digit(r, 3)}.{_digit(r, 1)}-{_digit(r, 3)}.{_digit(r, 3)}",
                          "tmt_asal": tmt_asal, "tmt_pindah": tmt_pindah})
            k += 1
    return orang


# ===================================================================== Angkasa Biru
JUMLAH_AP = 7500

BANDARA = [("CGK", "Bandara Soekarno-Hatta", "Tangerang"), ("DPS", "Bandara I Gusti Ngurah Rai", "Badung"),
           ("SUB", "Bandara Juanda", "Sidoarjo"), ("UPG", "Bandara Sultan Hasanuddin", "Makassar"),
           ("KNO", "Bandara Kualanamu", "Deli Serdang"), ("JOG", "Bandara Yogyakarta International", "Kulon Progo"),
           ("BPN", "Bandara Sultan Aji Muhammad Sulaiman", "Balikpapan"), ("SRG", "Bandara Ahmad Yani", "Semarang"),
           ("PLM", "Bandara Sultan Mahmud Badaruddin II", "Palembang"), ("MDC", "Bandara Sam Ratulangi", "Manado"),
           ("PDG", "Bandara Minangkabau", "Padang"), ("SOC", "Bandara Adi Soemarmo", "Boyolali"),
           ("LOP", "Bandara Lombok", "Praya"), ("PKU", "Bandara Sultan Syarif Kasim II", "Pekanbaru"),
           ("BDJ", "Bandara Syamsudin Noor", "Banjarbaru"), ("PNK", "Bandara Supadio", "Kubu Raya"),
           ("AMQ", "Bandara Pattimura", "Ambon"), ("DJJ", "Bandara Sentani", "Jayapura"),
           ("HO", "Kantor Pusat", "Jakarta Pusat")]
DIREKTORAT_AP = [("DU", "Utama"), ("WD", "Wakil Direktur Utama"), ("DO", "Operasi"), ("DT", "Teknik"),
                 ("DH", "Human Capital"), ("DK", "Komersial"), ("DF", "Keuangan dan Manajemen Risiko"),
                 ("DS", "Strategi & Pengembangan Teknologi")]


def bangun_angkasabiru() -> dict:
    r0 = _rng("ap-master")
    data = {}

    data["regions"] = [{"region_id": i + 1, "region_code": f"REG{i + 1}", "region_name": f"Region {i + 1}"}
                       for i in range(9)]
    data["branches"] = [
        {"CODE_AREA": kode, "NAME_ALIAS": kode, "NAME_AREA": nama, "CITY": kota,
         "REGION": f"REG{(i % 9) + 1}", "CODE_SUBHOLDING": "AB", "IS_MEMBER": "1",
         "CAT": "BANDARA" if kode != "HO" else "KANTOR", "KELAS_BANDARA": str((i % 3) + 1),
         "KELAS_BANDARA_INJ": str((i % 3) + 1), "ACTIVE_NON_ACTIVE": "AKTIF",
         "STATUS_DATA": "FINAL", "SUBAREA": None, "LISTAREA_ABSENCE": kode}
        for i, (kode, nama, kota) in enumerate(BANDARA)]
    data["directorates"] = [{"directorate_id": i + 1, "code_directorat": kode, "name_directorat": nama}
                            for i, (kode, nama) in enumerate(DIREKTORAT_AP)]
    data["groups"] = []
    for i in range(60):
        kode_area = BANDARA[i % len(BANDARA)][0]
        kode_dir = DIREKTORAT_AP[i % len(DIREKTORAT_AP)][0]
        data["groups"].append({"code_group": f"GRP{i + 1:03d}", "name_group": f"Group {BIDANG[i % len(BIDANG)]} {i + 1}",
                               "code_area": kode_area, "code_directorate": kode_dir, "Lokasi_Kerja": kode_area})
    data["job_families"] = [{"id_job_family": f"JF{i + 1:02d}", "job_family_name": b,
                             "job_family_description": f"Rumpun jabatan {b}"} for i, b in enumerate(BIDANG[:14] + ["Audit", "Umum"][:max(0, 14 - len(BIDANG))])]
    data["job_functions"] = [{"id_job_function": f"JFN{i + 1:02d}", "fk_job_family_id": jf["id_job_family"],
                              "job_function_name": f"Fungsi {jf['job_family_name']}",
                              "job_function_type": "Fungsional", "job_function_description": None}
                             for i, jf in enumerate(data["job_families"])]
    data["position_types"] = [{"id_position_type": "PT1", "position_type_name": "Struktural"},
                              {"id_position_type": "PT2", "position_type_name": "Fungsional"},
                              {"id_position_type": "PT3", "position_type_name": "Pelaksana"}]

    # unit organisasi: pohon 4 level (puncak id = induk, level anak = level induk + 1)
    units = [{"id_org_unit": "1", "id_parent_org_unit": "1", "org_level": 1,
              "org_unit_name": "PT Angkasa Biru", "cost_center": "CC0001"}]
    nid = 2
    for d_kode, d_nama in DIREKTORAT_AP:
        induk_dir = str(nid)
        units.append({"id_org_unit": induk_dir, "id_parent_org_unit": "1", "org_level": 2,
                      "org_unit_name": f"Direktorat {d_nama}", "cost_center": f"CC{nid:04d}"})
        nid += 1
        for b in range(6):
            induk_div = str(nid)
            units.append({"id_org_unit": induk_div, "id_parent_org_unit": induk_dir, "org_level": 3,
                          "org_unit_name": f"Divisi {BIDANG[(nid + b) % len(BIDANG)]} {d_kode}{b + 1}",
                          "cost_center": f"CC{nid:04d}"})
            nid += 1
            for u in range(5):
                units.append({"id_org_unit": str(nid), "id_parent_org_unit": induk_div, "org_level": 4,
                              "org_unit_name": f"Unit {BIDANG[(nid + u) % len(BIDANG)]} {nid}",
                              "cost_center": f"CC{nid:04d}"})
                nid += 1
    data["units"] = units
    unit_level4 = [u for u in units if u["org_level"] == 4]

    # posisi: code_position = id_position_master; satu varian per posisi (id varian berbeda dari kode master)
    posisi, master, varian, kompetensi_posisi = [], [], [], []
    for i in range(800):
        r = _rng("ap-pos", i)
        kode = f"PA{i + 1:04d}"
        area = BANDARA[i % len(BANDARA)][0]
        grp = data["groups"][i % len(data["groups"])]
        d_kode = grp["code_directorate"]
        fungsi = FUNGSI_POSISI[i % len(FUNGSI_POSISI)]
        bidang = BIDANG[i % len(BIDANG)]
        nama = f"{fungsi} {bidang} {area}"
        job_class = r.choice([7, 8, 9, 10, 11, 12, 13, 13, 14, 15, 16, 17, 18])
        unit = unit_level4[i % len(unit_level4)]
        posisi.append({"code_position": kode, "name_position": nama, "area": area,
                       "code_directorate": d_kode, "code_group": grp["code_group"],
                       "code_division": f"DIV{(i % 48) + 1:02d}", "position_level": str(job_class),
                       "position_type": data["position_types"][i % 3]["position_type_name"]})
        master.append({"id_position_master": kode, "position_master_name": nama,
                       "fk_position_type_id": data["position_types"][i % 3]["id_position_type"],
                       "id_grade": str(job_class), "id_job_family": data["job_families"][i % len(data["job_families"])]["id_job_family"],
                       "id_job_function": data["job_functions"][i % len(data["job_functions"])]["id_job_function"],
                       "active_status": "1"})
        # id varian == id master == code_position, meniru API asli (riwayat posisi memakai kode yang sama)
        varian.append({"id_position_variant": kode, "fk_position_master_id": kode,
                       "position_variant_name": nama, "fk_org_unit_id": unit["id_org_unit"],
                       "job_class": str(job_class), "max_active_employee": r.choice([1, 1, 2, 5, 20]),
                       "is_job_assignment": "0", "dt_active": "2024-01-01", "dt_inactive": None,
                       "active_status": "1"})
        for k_idx in r.sample(range(len(KOMPETENSI)), 5):
            nama_k, kat = KOMPETENSI[k_idx]
            kompetensi_posisi.append({"fk_position_id": kode, "id_competency": f"K{k_idx + 1:02d}",
                                      "competetency_name": KOMPETENSI_BAKU[nama_k], "competency_category": kat,
                                      "required_level": str(r.randrange(1, 6))})
    data["positions"], data["position_master"], data["position_variants"] = posisi, master, varian
    data["position_competency_requirements"] = kompetensi_posisi

    # master perusahaan (kosong di API asli)
    data["companies"] = [{"id_company": "AB-001", "company_name": "PT Angkasa Biru",
                          "company_type": "Holding", "dt_establishment": "2023-12-28",
                          "address": "Jl. M.H. Thamrin No. 11", "city": "Jakarta Pusat",
                          "province": "DKI Jakarta", "postal_code": "10350",
                          "email": "corporate@angkasabiru.id", "phone": "021-6541961",
                          "website": "https://angkasabiru.id"}]
    data["company_types"] = [{"id_company_type": "HOLD", "company_type_name": "Holding"},
                             {"id_company_type": "MEMB", "company_type_name": "Member"}]
    data["company_addresses"] = [{"id_company_address": "AB-ADDR-001", "fk_company_id": "AB-001",
                                  "street_address": "Jl. M.H. Thamrin No. 11", "sub_district": "Kebon Sirih",
                                  "district": "Menteng", "city": "Jakarta Pusat", "province": "DKI Jakarta",
                                  "postal_code": "10350"}]
    data["company_documents"] = [{"id_company_document": "AB-DOC-001", "fk_company_id": "AB-001",
                                  "document_type": "Akta Pendirian",
                                  "document_number": "AHU-0075321.AH.01.01", "dt_document": "2023-12-28"}]
    data["divisions"] = [{"code_division": f"DIV{i + 1:02d}", "name_division": f"Divisi {BIDANG[i % len(BIDANG)]}"}
                         for i in range(48)]
    data["bands"] = [{"id_band": f"AB-BAND-{i}", "band_name": f"Band {i}", "band_sequence": i,
                      "band_category": kat, "job_class_min": lo, "job_class_max": hi,
                      "compensation_min": None, "compensation_max": None,
                      "description": f"Band {i} ({kat}), job class {lo}-{hi}"}
                     for i, (kat, lo, hi) in enumerate([("Executive", 18, 23), ("Senior Managerial", 16, 17),
                                                        ("Managerial", 14, 15), ("Operational", 7, 13)], start=1)]

    # ------------------------------------------------------------- pegawai
    profil, identifikasi, alamat, keluarga, pendidikan = [], [], [], [], []
    riwayat_posisi, penugasan, kinerja, pembelajaran, cuti = [], [], [], [], []
    comp = []
    tmt_csv, nominatif_csv, master_csv = [], [], []
    niks = []
    for i in range(JUMLAH_AP):
        r = _rng("ap-peg", i)
        tahun_masuk = r.randrange(1990, 2026)
        nik = f"{tahun_masuk}{i:04d}"[:8].ljust(8, "0")
        niks.append(nik)
        nama = _nama(r)
        # semua pegawai AB aktif: tahun lahir >= 1969 agar belum melewati usia pensiun 58
        lahir = _tanggal(r, date(max(1969, tahun_masuk - 40), 1, 1), date(min(2004, tahun_masuk - 18), 12, 28))
        tmt = _tanggal(r, date(tahun_masuk, 1, 1), date(tahun_masuk, 12, 28))
        kota = r.choice(KOTA)
        email = _email(nama, "angkasabiru.id", r)
        profil.append({"new_nip": nik, "old_nip": f"{_digit(r, 7)}", "full_name": nama,
                       "name_alias": nama.split()[0], "academic_title": r.choice(GELAR),
                       "corporate_email": email, "employee_status": "Aktif"})
        tmt_csv.append({"new_nip": nik, "tanggal_lahir": lahir.isoformat(), "tmt_karyawan": tmt.isoformat()})

        identifikasi.append({"id_employee": nik, "id_nik": _digit(r, 16), "id_npwp": f"{_digit(r, 2)}.{_digit(r, 3)}.{_digit(r, 3)}.{_digit(r, 1)}-{_digit(r, 3)}.{_digit(r, 3)}",
                             "birth_place": kota, "blood_type": r.choice(["A", "B", "AB", "O"]),
                             "gender": r.choice(["Laki-Laki", "Perempuan"]),
                             "ethnicity": None, "corporate_email": email,
                             "dt_start_work": tmt.isoformat(), "dt_appointed_employee": tmt.isoformat(),
                             "dt_grade_start": None,            # diisi dari baris riwayat posisi terakhir di bawah
                             "dt_retirement": _pensiun(lahir, 58).isoformat(),
                             "employment_type": r.choice(["PKWTT", "PKWTT", "PKWTT", "PKWTT", "PKWT"]),
                             "home_phone": _ponsel(r),
                             "id_bpjs_kes": _digit(r, 13), "id_bpjs_tk": _digit(r, 11)})
        alamat.append({"nik_new": nik, "Alamat": f"Jl. {r.choice(BELAKANG)} No. {r.randrange(1, 200)}, {kota}",
                       "address_type": "Alamat Tetap", "city": kota, "district": None,
                       "province": PROVINSI[kota], "postal_code": _digit(r, 5)})

        for j in range(r.randrange(0, 4)):
            rk = _rng("ap-kel", nik, j)
            keluarga.append({"id_family_member": f"FM-{nik}-{j + 1}", "id_employee": nik,
                             "full_name": _nama(rk), "relationship_type": "Suami/Istri" if j == 0 else "Anak",
                             "gender": rk.choice(["Laki-Laki", "Perempuan"]),
                             "dt_birth": _tanggal(rk, date(1970, 1, 1), date(2020, 12, 28)).isoformat(),
                             "birth_place": rk.choice(KOTA), "dt_marriage": None, "id_number": None,
                             "id_type": None, "marital_status": None, "nationality": "Indonesia"})
        for j in range(r.randrange(1, 3)):
            rp = _rng("ap-edu", nik, j)
            jen = rp.choice(["SLTA", "DIII - Diploma III", "S1 - Strata 1", "S1 - Strata 1", "S2 - Strata 2"])
            data_edu = {"id_emloyee": nik, "education_degree_type": jen,
                        "education_level_code": None, "institution_name": rp.choice(UNIVERSITAS),
                        "major": rp.choice(JURUSAN), "faculty": None,
                        "dt_start": str(lahir.year + 18 + j * 4), "dt_end": str(lahir.year + 22 + j * 4),
                        "final_score": round(rp.uniform(2.8, 3.9), 2),
                        "institution_country": "Indonesia", "certificate_number": None}
            pendidikan.append(data_edu)

        # riwayat posisi: 1-4 baris; semua baris menunjuk varian yang ada di master (referential integrity)
        n_riwayat = r.randrange(1, 5)
        mulai = tmt
        for j in range(n_riwayat):
            rv = _rng("ap-pos-hist", nik, j)
            v = varian[rv.randrange(len(varian))]
            fk = v["id_position_variant"]
            riwayat_posisi.append({"id_position_history": str(len(riwayat_posisi) + 1), "new_nip": nik,
                                   "employee_name": nama, "fk_position_variant_id": fk,
                                   "position_name": v["position_variant_name"], "position_type": None,
                                   "job_class": v["job_class"], "org_unit_name": None,
                                   "company_name": "AB", "dt_position_start": mulai.isoformat(),
                                   "dt_position_end": None})
            mulai = _tanggal(rv, mulai, date(2026, 9, 1)) if mulai < date(2026, 9, 1) else mulai
        identifikasi[-1]["dt_grade_start"] = riwayat_posisi[-1]["dt_position_start"]

        for tahun in (2023, 2024, 2025):
            if tmt.year > tahun:
                continue
            rp = _rng("ap-perf", nik, tahun)
            kinerja.append({"id_employee": nik, "NAMA": nama, "period_year": tahun,
                            "performance_score": None,
                            "performance_rating": rp.choices(["Partially Successful", "Successful", "Excellence", "Outstanding"],
                                                             weights=[10, 60, 20, 10])[0],
                            "pct_kpi_achievement": round(rp.uniform(70, 120), 1)})

        pilihan = PELATIHAN_WAJIB + r.sample(PELATIHAN_UMUM, r.randrange(3, 7))
        for j, (nama_l, jenis) in enumerate(pilihan):
            rl = _rng("ap-learn", nik, j)
            wajib = jenis == "Penjenjangan"
            selesai = rl.random() < 0.85
            dt_sel = _tanggal(rl, max(tmt, date(2022, 1, 1)), date(2026, 9, 30)) if selesai and tmt < date(2026, 9, 1) else None
            pembelajaran.append({"id_employee": nik, "NAMA": nama, "id_learning": f"LRN-AB-{nik}-{j + 1}",
                                 "learning_name": nama_l, "learning_type": jenis, "is_mandatory": wajib,
                                 "dt_completion": dt_sel.isoformat() if dt_sel else None,
                                 "dt_expiry": (dt_sel + timedelta(days=730)).isoformat() if dt_sel and wajib else None,
                                 "score": round(rl.uniform(70, 95), 1) if dt_sel else None,
                                 "learning_hours": rl.choice([8, 16, 24, 32, 40]),
                                 "provider": rl.choice(PENYEDIA)})

        for j in range(r.randrange(1, 6)):
            rc = _rng("ap-cuti", nik, j)
            mulai_c = _tanggal(rc, date(2025, 1, 1), date(2026, 9, 30))
            hari = rc.randrange(1, 13)
            atasan = niks[rc.randrange(max(1, len(niks) - 1))] if len(niks) > 1 else nik
            cuti.append({"id_leave_history": f"LV-AB-{nik}-{j + 1}", "id_employee": nik, "Nama": nama,
                         "leave_type": rc.choice(["Leave", "Leave", "Leave", "Absence"]),
                         "dt_leave_start": mulai_c.isoformat(),
                         "dt_leave_end": (mulai_c + timedelta(days=hari - 1)).isoformat(),
                         "leave_duration_days": hari, "leave_reason": None,
                         "leave_status": rc.choice(["Full Approve", "Full Approve", "Approve Atasan", "Pengajuan"]),
                         "approve_by": f"{atasan}, {niks[0]}"})

        if r.random() < 0.03:
            ra = _rng("ap-asg", nik)
            v = varian[ra.randrange(len(varian))]
            mulai_a = _tanggal(ra, date(2024, 1, 1), date(2026, 6, 30))
            penugasan.append({"id_assignment_history": str(len(penugasan) + 1), "id_employee": nik,
                              "assignment_name": ra.choice(["PGS", "PH"]),
                              "assignment_position": v["position_variant_name"],
                              "assignment_letter_number": f"SK-{_digit(ra, 4)}/{mulai_a.year}",
                              "dt_assignment_start": mulai_a.isoformat(),
                              "dt_assignment_end": (mulai_a + timedelta(days=90)).isoformat(),
                              "assignment_duration_months": 3})

        rj = _rng("jobfit-ap", nik)
        for periode in PERIODE:
            if periode == PERIODE[0] and rj.random() < 0.2:
                continue
            comp.append({"id_employee": nik, "assessment_period": periode,
                         "job_fit_score": round(rj.uniform(60, 95), 1),
                         "competency_gap": round(rj.uniform(-15, 10), 1),
                         "assessment_method": rj.choice(METODE_ASES),
                         "dt_assessment": _tanggal(rj, date(2025, 7, 1) if periode == PERIODE[0] else date(2026, 1, 1),
                                                   date(2025, 12, 20) if periode == PERIODE[0] else date(2026, 6, 30)).isoformat()})
        master_csv.append({"Kode Perusahaan": "AB", "NIK": nik,
                           "Top Talent": "Ya" if _rng("ap-tt", nik).random() < 0.014 else "Tidak"})
        if r.random() < 0.75:
            # nominatif: jabatan = posisi terkini (nama sama dengan riwayat terakhir) supaya aturan pencocokan terpakai
            baris_akhir = riwayat_posisi[-1]
            v_unit = next((u for u in unit_level4 if u["id_org_unit"] ==
                           next((vv["fk_org_unit_id"] for vv in varian if vv["id_position_variant"] == baris_akhir["fk_position_variant_id"]), None)), None)
            nominatif_csv.append({"nik_baru": nik, "nama_jabatan": baris_akhir["position_name"],
                                  "unit": v_unit["org_unit_name"] if v_unit else None,
                                  "area": baris_akhir["position_name"].split()[-1],
                                  "direktorat": r.choice(DIREKTORAT_AP)[0]})

    # Talent Mobility: AB sebagai perusahaan asal (diperbantukan keluar) atau tujuan (diperbantukan masuk)
    for o in _daftar_mobilitas():
        if "AB" not in (o["asal"], o["tujuan"]):
            continue
        asal = o["asal"] == "AB"
        r = _rng("ap-mob", o["k"])
        tmt = o["tmt_asal"] if asal else o["tmt_pindah"]
        nik = f"{tmt.year}{7500 + o['k']:04d}"
        nama = o["nama"]
        email = _email(nama, "angkasabiru.id", r)
        profil.append({"new_nip": nik, "old_nip": _digit(r, 7), "full_name": nama,
                       "name_alias": nama.split()[0], "academic_title": r.choice(GELAR),
                       "corporate_email": email,
                       "employee_status": "Diperbantukan" if asal else "Aktif"})
        identifikasi.append({"id_employee": nik, "id_nik": o["id_nik"], "id_npwp": o["id_npwp"],
                             "birth_place": o["kota"], "blood_type": r.choice(["A", "B", "AB", "O"]),
                             "gender": "Laki-Laki" if o["gender"] == "L" else "Perempuan",
                             "ethnicity": None, "corporate_email": email,
                             "dt_start_work": tmt.isoformat(), "dt_appointed_employee": tmt.isoformat(),
                             "dt_grade_start": tmt.isoformat(),
                             "dt_retirement": _pensiun(o["lahir"], 58).isoformat(),
                             "employment_type": "PKWTT",       # Talent Mobility pasti PKWTT, di asal maupun tujuan
                             "home_phone": _ponsel(r),
                             "id_bpjs_kes": _digit(r, 13), "id_bpjs_tk": _digit(r, 11)})
        alamat.append({"nik_new": nik, "Alamat": f"Jl. {r.choice(BELAKANG)} No. {r.randrange(1, 200)}, {o['kota']}",
                       "address_type": "Alamat Tetap", "city": o["kota"], "district": None,
                       "province": PROVINSI[o["kota"]], "postal_code": _digit(r, 5)})
        v = varian[r.randrange(len(varian))]
        riwayat_posisi.append({"id_position_history": str(len(riwayat_posisi) + 1), "new_nip": nik,
                               "employee_name": nama, "fk_position_variant_id": v["id_position_variant"],
                               "position_name": v["position_variant_name"], "position_type": None,
                               "job_class": v["job_class"], "org_unit_name": None,
                               "company_name": "AB", "dt_position_start": tmt.isoformat(),
                               "dt_position_end": o["tmt_pindah"].isoformat() if asal else None})
        tmt_csv.append({"new_nip": nik, "tanggal_lahir": o["lahir"].isoformat(), "tmt_karyawan": tmt.isoformat()})
        master_csv.append({"Kode Perusahaan": "AB", "NIK": nik, "Top Talent": "Tidak"})

    data["employee_profile"] = profil
    data["employee_identification"] = identifikasi
    data["employee_address"] = alamat
    data["employee_family_member"] = keluarga
    data["employee_education_history"] = pendidikan
    data["employee_position_history"] = riwayat_posisi
    data["employee_assignment_history"] = penugasan
    data["employee_performance"] = kinerja
    data["employee_learning"] = pembelajaran
    data["employee_leave_history"] = cuti
    data["competency_assessment"] = comp
    _jamin_lengkap(profil, "new_nip", identifikasi, "id_employee", riwayat_posisi, "new_nip", "angkasabiru")
    data["_tmt_csv"], data["_nominatif_csv"], data["_master_csv"] = tmt_csv, nominatif_csv, master_csv
    return data


# ===================================================================== Angkasa Biru Retail
JUMLAH_SNH_PROFIL = 440
JUMLAH_SNH_HANYA_EMPLOYEES = 0   # placeholder: semua pegawai punya profil + detail (tidak ada status tidak diketahui)

AREA_SNH = [("1000", "Kantor Pusat"), ("2000", "Angkasa Biru Retail Thamrin"), ("3000", "Angkasa Biru Retail Malang"),
            ("4000", "Angkasa Biru Retail Braga"), ("5000", "Duty Free"), ("6000", "Ritel Digital")]
DIREKTORAT_SNH = ["Direktorat Utama", "Direktorat Keuangan", "Direktorat Komersial",
                  "Direktorat Operasional", "Direktorat Human Capital"]


def bangun_angkasabiruretail() -> dict:
    data = {}
    data["companies"] = [{"id_company": "1", "company_name": "PT Angkasa Biru Retail", "company_type": "Member",
                          "dt_establishment": "1962-08-17", "address": "Jl. M.H. Thamrin No. 11",
                          "city": "Jakarta Pusat", "province": "DKI Jakarta", "postal_code": "10350",
                          "email": "corsec@angkasabiruretail.id", "phone": "021-39831234",
                          "website": "https://angkasabiruretail.id"}]
    data["company_addresses"] = [{"id_company": "1", "fk_company_id": "1", "code_subholding": "ABR",
                                  "street_address": "Jl. M.H. Thamrin No. 11", "sub_district": "Kebon Sirih",
                                  "district": "Menteng", "city": "Jakarta Pusat", "province": "DKI Jakarta",
                                  "postal_code": "10350"}]
    data["areas"] = [{"id": i + 1, "code_area": kode, "name_area": nama, "name_alias": nama,
                      "code_subholding": "ABR", "cat": "RITEL", "is_member": 1, "region": "REG1"}
                     for i, (kode, nama) in enumerate(AREA_SNH)]
    data["directorates"] = [{"id": i + 1, "code_directorate": f"D{i + 1}", "name_directorate": nama,
                             "code_area": "1000", "code_subholding": "ABR", "status_aktif": "aktif"}
                            for i, nama in enumerate(DIREKTORAT_SNH)]
    data["groups"] = [{"id": i + 1, "code_group": f"G{i + 1:02d}", "name_group": f"Group {BIDANG[i % len(BIDANG)]}",
                       "code_directorate": f"D{(i % 5) + 1}", "code_area": AREA_SNH[i % 6][0],
                       "code_subholding": "ABR", "status_aktif": "aktif"} for i in range(20)]
    data["bands"] = [{"id_band": f"ABR-BAND-{i}", "band_name": f"Band {i}", "band_sequence": i,
                      "band_category": kat, "job_class_min": lo, "job_class_max": hi,
                      "compensation_min": None, "compensation_max": None,
                      "description": f"Band {i} ({kat}), job class {lo}-{hi}",
                      "created_at": None, "updated_at": None}
                     for i, (kat, lo, hi) in enumerate([("Executive", 17, 23), ("Senior Managerial", 14, 16),
                                                        ("Managerial", 12, 13), ("Operational", 7, 11)], start=1)]
    data["grades"] = [{"id": i + 1, "grade_min": str(i + 1), "grade_max": str(i + 1),
                       "grade_notes": f"Grade {i + 1}", "code_subholding": "ABR"} for i in range(25)]
    data["position_levels"] = [{"id": i + 1, "code_position_level": f"PL{i + 1:02d}",
                                "name_position_level": f"Level {i + 1}"} for i in range(16)]
    data["position_types"] = [{"id": i + 1, "code_position_type": f"PT{i + 1}", "name_position_type": n}
                              for i, n in enumerate(["Struktural", "Fungsional", "Pelaksana", "Kontrak", "Penugasan"])]
    data["job_families"] = [{"id": i + 1, "code_job_family": f"SJF{i + 1:02d}", "name_job_family": b,
                             "job_family_description": f"Rumpun {b}"} for i, b in enumerate(BIDANG)]
    data["job-function"] = [{"id_job_function": "SJFN01", "fk_job_family_id": "SJF01",
                             "job_family_name": BIDANG[0], "job_function_name": f"Fungsi {BIDANG[0]}",
                             "job_function_type": "Fungsional", "job_function_description": None,
                             "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z"}]
    data["competences"] = [{"id": i + 1, "code": f"K{i + 1:02d}", "competency": nama,
                            "type": KATEGORI_KOMPETENSI[kat], "competency_align": None, "code_subholding": "ABR"}
                           for i, (nama, kat) in enumerate(KOMPETENSI)]
    data["org-unit-types"] = [{"id_org_unit_type": i + 1, "org_unit_type_name": n,
                               "created_at": None, "updated_at": None}
                              for i, n in enumerate(["Direktorat", "Divisi", "Departemen", "Seksi", "Store", "Proyek"])]

    units = [{"id_org_unit": "1", "id_parent_org_unit": "1", "org_level": 1, "org_unit_name": "PT Angkasa Biru Retail",
              "cost_center": "S0001", "fk_id_company": "1", "dwh_source_system": None,
              "created_at": None, "updated_at": None}]
    nid = 2
    for d in DIREKTORAT_SNH:
        induk = str(nid)
        units.append({"id_org_unit": induk, "id_parent_org_unit": "1", "org_level": 2, "org_unit_name": d,
                      "cost_center": f"S{nid:04d}", "fk_id_company": "1", "dwh_source_system": None,
                      "created_at": None, "updated_at": None})
        nid += 1
        for b in range(4):
            induk_div = str(nid)
            units.append({"id_org_unit": induk_div, "id_parent_org_unit": induk, "org_level": 3,
                          "org_unit_name": f"Divisi {BIDANG[(nid + b) % len(BIDANG)]} {nid}",
                          "cost_center": f"S{nid:04d}", "fk_id_company": "1", "dwh_source_system": None,
                          "created_at": None, "updated_at": None})
            nid += 1
            for u in range(4):
                units.append({"id_org_unit": str(nid), "id_parent_org_unit": induk_div, "org_level": 4,
                              "org_unit_name": f"Departemen {BIDANG[(nid + u) % len(BIDANG)]} {nid}",
                              "cost_center": f"S{nid:04d}", "fk_id_company": "1", "dwh_source_system": None,
                              "created_at": None, "updated_at": None})
                nid += 1
    data["org-units"] = units
    unit_bawah = [u for u in units if u["org_level"] == 4]

    posisi, varian = [], []
    for i in range(400):
        r = _rng("snh-pos", i)
        kode = f"SN{i + 1:04d}"
        fungsi = FUNGSI_POSISI[i % len(FUNGSI_POSISI)]
        bidang = BIDANG[i % len(BIDANG)]
        area = AREA_SNH[i % 6]
        nama = f"{fungsi} {bidang} {area[1]}"
        jc = r.choice([7, 8, 9, 10, 11, 11, 12, 13, 14, 15, 16, 17])
        posisi.append({"code_position": kode, "name_position": nama, "code_job_family": f"SJF{(i % len(BIDANG)) + 1:02d}",
                       "code_job_family_2": None, "code_job_family_3": None,
                       "code_position_level": f"PL{(i % 16) + 1:02d}", "code_position_type": f"PT{(i % 3) + 1}",
                       "grade_min": str(jc), "band_min": None, "band_max": None, "band_notes": None,
                       "area": area[0], "code_directorate": f"D{(i % 5) + 1}", "code_division": None,
                       "code_group": f"G{(i % 20) + 1:02d}", "code_subholding": "ABR", "status_aktif": "aktif"})
        if True:   # placeholder: semua posisi punya varian agar unit pegawai dapat ditelusuri
            varian.append({"id_position_variant": kode, "fk_position_master_id": f"PM_{kode}",
                           "position_variant_name": nama, "fk_org_unit_id": unit_bawah[i % len(unit_bawah)]["id_org_unit"],
                           "job_class": str(jc), "max_active_employee": 3, "is_job_assignment": "0",
                           "dt_active": "2024-01-01T00:00:00.000Z", "dt_inactive": None,
                           "created_at": None, "updated_at": None})
    data["positions"], data["position-variants"] = posisi, varian

    # ------------------------------------------------------------- pegawai
    profil, rinci, roster, alamat_b, kontrak = [], [], [], [], []
    pasangan, anak, pendidikan, sertifikat, riwayat, kinerja = [], [], [], [], [], []
    hukdis, asesmen, asesmen_anak, pelatihan_lama, pembelajaran, cuti_b = [], [], [], [], [], []
    master_csv = []
    semua_nip = []
    for i in range(JUMLAH_SNH_PROFIL + JUMLAH_SNH_HANYA_EMPLOYEES):
        r = _rng("snh-peg", i)
        nip = f"{r.randrange(0, 2)}{_digit(r, 6)}"      # 7 digit, sebagian berawalan 0
        while nip in semua_nip:
            nip = f"{r.randrange(0, 2)}{_digit(r, 6)}"
        semua_nip.append(nip)
        id_sistem = f"EMP-{i + 1:04d}"
        nama = _nama(r)
        aktif = r.random() >= 0.055                      # ±25 resigned
        # pegawai aktif: tahun lahir >= 1971 agar belum melewati usia pensiun 56; yang resigned boleh lebih tua
        lahir = _tanggal(r, date(1971 if aktif else 1966, 1, 1), date(2003, 12, 28))
        tmt = _tanggal(r, date(max(1990, lahir.year + 18), 1, 1), date(2026, 6, 30))
        email = _email(nama, "angkasabiruretail.id", r)
        area = AREA_SNH[i % 6]
        jc = r.choice(["7", "8", "9", "10", "11", "11", "12", "13", "14", "15", "16", "17"])
        hanya_roster = i >= JUMLAH_SNH_PROFIL

        roster.append({"code_member": nip, "personel_number": nama, "email": email,
                       "status_aktif": "Active" if aktif else "Resigned", "photo_blob": None,
                       "person_grade": jc if jc != "4B" else None,
                       "personnel_area_text": area[0], "area_nomenklatur": area[1],
                       "name_directorate": DIREKTORAT_SNH[i % 5], "name_group": f"Group {BIDANG[i % len(BIDANG)]}",
                       "band_name": None, "code_directorate": f"D{(i % 5) + 1}", "code_division": None,
                       "code_group": f"G{(i % 20) + 1:02d}", "code_subholding": "ABR",
                       "birthplace": r.choice(KOTA), "date_of_birth": lahir.isoformat(),
                       "division": None, "education_level": None, "gender_text": r.choice(["Male", "Female"]),
                       "home_address": f"Jl. {r.choice(BELAKANG)} No. {r.randrange(1, 150)}"})
        if not hanya_roster:
            profil.append({"id_employee": id_sistem, "old_nip": nip, "new_nip": _digit(r, 8),
                           "full_name": nama, "name_alias": nama.split()[0],
                           "academic_title": r.choice(GELAR), "corporate_email": email,
                           "employment_status": "Active" if aktif else "Resigned",
                           "photo_blob": None, "leave_type": None,
                           "created_at": None, "updated_at": None})
            rinci.append({"id_employee": id_sistem, "employee_name": nama, "id_nik": _digit(r, 16),
                          "id_npwp": f"{_digit(r, 2)}.{_digit(r, 3)}.{_digit(r, 3)}.{_digit(r, 1)}-{_digit(r, 3)}.{_digit(r, 3)}",
                          "birth_place": r.choice(KOTA), "dt_birth": lahir.isoformat(),
                          "dt_start_work": tmt.isoformat(), "dt_retirement": _pensiun(lahir, 56).isoformat(),
                          "dt_appointed_employee": tmt.isoformat(),
                          "dt_grade_start": _tanggal(r, tmt, date(2026, 6, 30)).isoformat(),
                          "employment_type": r.choice(["PKWTT", "PKWTT", "PKWT"]),
                          "job_class": jc, "gender": r.choice(["Male", "Female"]),
                          "mobile_phone": "+62" + _ponsel(r)[1:], "corporate_email": email,
                          "blood_type": r.choice(["A", "B", "AB", "O"]), "ethnicity": None,
                          "home_phone": None})
            kota_rumah = r.choice(KOTA)
            alamat_b.append({"id_employee": id_sistem, "old_nip": nip, "employee_name": nama,
                             "address_type": "alamat_tetap",
                             "street_address": f"Jl. {r.choice(BELAKANG)} No. {r.randrange(1, 150)}",
                             "city": kota_rumah, "district": None, "province": PROVINSI[kota_rumah],
                             "postal_code": _digit(r, 5), "country": "Indonesia",
                             "geo_latitude": None, "geo_longitude": None, "created_at": None, "updated_at": None})
            mulai_k = _tanggal(r, tmt, date(2026, 6, 30))
            kontrak.append({"id_contract": f"CT-{i + 1:04d}", "id_employee": id_sistem, "old_nip": nip,
                            "employee_name": nama, "corporate_email": email,
                            "contract_number": f"KTR/{mulai_k.year}/{_digit(r, 4)}",
                            "contract_type": r.choice(["pkwtt", "pkwtt", "pkwt"]),
                            "contract_status": "active" if aktif else "terminated",
                            "dt_contract_start": mulai_k.isoformat(),
                            "dt_contract_end": (mulai_k + timedelta(days=730)).isoformat() if r.random() < 0.35 else None,
                            "dt_probation_start": mulai_k.isoformat(),
                            "dt_probation_end": (mulai_k + timedelta(days=r.choice([45, 60, 75]))).isoformat(),
                            "contract_renewal_count": r.randrange(0, 3), "created_at": None, "updated_at": None})

        if r.random() < 0.4:
            rs = _rng("snh-spouse", nip)
            pasangan.append({"id": 100000 + len(pasangan) + 1, "nik": str(int(nip)), "employee_id": id_sistem,
                             "nama": _nama(rs), "jns_kelamin": rs.choice(["Male", "Female"]),
                             "tgl_lahir": _tanggal(rs, date(1968, 1, 1), date(2000, 12, 28)).strftime("%d/%m/%Y"),
                             "tmp_lahir": rs.choice(KOTA), "tgl_menikah": None, "pekerjaan": None,
                             "keterangan": None, "code_subholding": "ABR"})
        for j in range(_rng("snh-anak-n", nip).randrange(0, 3)):
            ra = _rng("snh-anak", nip, j)
            anak.append({"id": 200000 + len(anak) + 1, "nik": str(int(nip)), "employee_id": id_sistem,
                         "nama": _nama(ra), "jns_kelamin": ra.choice(["Male", "Female"]),
                         "tgl_lahir": _tanggal(ra, date(1995, 1, 1), date(2024, 12, 28)).strftime("%d/%m/%Y"),
                         "tmp_lahir": ra.choice(KOTA), "tgl_menikah": None, "pekerjaan": None,
                         "keterangan": None, "code_subholding": "ABR"})
        for j in range(r.randrange(1, 3)):
            re_ = _rng("snh-edu", nip, j)
            pendidikan.append({"nik": str(int(nip)),
                               "level_education": re_.choice(["Senior High School", "Associate Degree 3 (D3)",
                                                              "Bachelor Degree (S1)", "Bachelor Degree (S1)",
                                                              "Master Degree (S2)"]),
                               "university_name": re_.choice(UNIVERSITAS), "major_name": re_.choice(JURUSAN),
                               "ipk": round(re_.uniform(2.8, 3.9), 2),
                               "start_date": str(lahir.year + 18), "end_date": str(lahir.year + 22),
                               "tahun_lulus": str(lahir.year + 22), "kota_negara": None,
                               "penghargaan": None, "code_subholding": "ABR"})
        if r.random() < 0.15:
            rc = _rng("snh-cert", nip)
            sertifikat.append({"id": len(sertifikat) + 1, "nik": str(int(nip)),
                               "certificate_name": "Sertifikasi Profesi " + rc.choice(BIDANG),
                               "certificate_number": f"CRT-{_digit(rc, 6)}", "certificate_type": "Profesi",
                               "institution_name": rc.choice(PENYEDIA), "country": "Indonesia",
                               "start_date": _tanggal(rc, date(2022, 1, 1), date(2025, 12, 1)).isoformat(),
                               "end_date": None, "job_family": rc.choice(BIDANG), "code_subholding": "ABR"})

        n_riwayat = r.randrange(1, 4)
        mulai_p = tmt
        for j in range(n_riwayat):
            rp = _rng("snh-pos-hist", nip, j)
            p = posisi[rp.randrange(len(posisi))]
            riwayat.append({"id": str(len(riwayat) + 1), "nik": str(int(nip)), "name": nama,
                            "position_code": p["code_position"], "position_name": p["name_position"],
                            "grade_name": p["grade_min"], "band_name": None,
                            "area_name": area[1], "directorate": DIREKTORAT_SNH[i % 5],
                            "division_name": f"Divisi {BIDANG[j % len(BIDANG)]}",
                            "job_family": BIDANG[i % len(BIDANG)], "is_current": "1" if j == n_riwayat - 1 else "0",
                            "start_date": mulai_p.isoformat(),
                            "end_date": None if j == n_riwayat - 1 else mulai_p.isoformat(),
                            "perusahaan": "PT. Angkasa Biru Retail", "achievement": None,
                            "desc_tugas_kewenangan": None, "code_subholding": "ABR"})
            mulai_p = _tanggal(rp, mulai_p, date(2026, 6, 1)) if mulai_p < date(2026, 6, 1) else mulai_p

        for tahun in (2023, 2024, 2025):
            if tmt.year > tahun:
                continue
            rp = _rng("snh-perf", nip, tahun)
            nilai = round(rp.uniform(2.8, 5.0), 2)
            kinerja.append({"id": f"PERF-{nip}-{tahun}", "nik": str(int(nip)), "year": tahun,
                            "period_label": f"Tahunan {tahun}", "performance_nilai": nilai,
                            "performance_scala": nilai,
                            "performance_category": rp.choice(["Successful", "Successful", "Excellent",
                                                               "Outstanding", "Partially Successful"]),
                            "code_subholding": "ABR"})

        if r.random() < 0.05:
            rh = _rng("snh-hukdis", nip)
            mulai_h = _tanggal(rh, date(2024, 1, 1), date(2026, 6, 30))
            hukdis.append({"id": len(hukdis) + 1, "nik": str(int(nip)),
                           "hukdis_cat": rh.choice(["Ringan", "Ringan", "Sedang", "Berat"]),
                           "start_date": mulai_h.isoformat(),
                           "end_date": (mulai_h + timedelta(days=180)).isoformat(),
                           "is_active": "1" if mulai_h > date(2026, 3, 1) else "0", "code_subholding": "ABR"})

        ras = _rng("jobfit-snh", nip)
        mulai_a = _tanggal(ras, date(2025, 1, 1), date(2026, 6, 30))
        id_ases = f"ASM-{nip}"
        asesmen.append({"id": id_ases, "nik": str(int(nip)), "code_subholding": "ABR",
                        "hasil_ases": ras.choice(["Disarankan", "Memenuhi Persyaratan", "Memenuhi Persyaratan",
                                                  "Memenuhi Persyaratan dengan Catatan", "Disarankan dengan Pengembangan",
                                                  "Dipertimbangkan", "Belum Memenuhi Persyaratan"]),
                        "berlaku_dari": mulai_a.isoformat(),
                        "berlaku_hingga": (mulai_a + timedelta(days=730)).isoformat(),
                        "posisi_tujuan_ases": None, "lembaga_ases": ras.choice(PENYEDIA),
                        "id_as_parent": None, "code_member": nip,
                        "assessment_method": ras.choice(METODE_ASES)})
        for j in range(ras.randrange(3, 7)):
            nama_k, _ = KOMPETENSI[ras.randrange(len(KOMPETENSI))]
            asesmen_anak.append({"id": len(asesmen_anak) + 1, "id_parent": id_ases, "nik": str(int(nip)),
                                 "result": round(ras.uniform(2.0, 5.0), 1), "soft_competency_member": nama_k,
                                 "competency_clasification": None, "jabatan_saat_ases": None,
                                 "lembaga_ases": None, "berlaku_dari": mulai_a.isoformat(),
                                 "berlaku_hingga": None, "keterangan_1": None, "keterangan_2": None,
                                 "prev_nik": None, "code_subholding": "ABR"})

        if r.random() < 0.6:
            rt = _rng("snh-train", nip)
            nama_t, jenis_t = rt.choice(PELATIHAN_UMUM)
            mulai_t = _tanggal(rt, date(2023, 1, 1), date(2026, 6, 30))
            pelatihan_lama.append({"id": len(pelatihan_lama) + 1, "nik": str(int(nip)),
                                   "training_name": nama_t, "training_type": jenis_t,
                                   "training_org": rt.choice(PENYEDIA), "city": rt.choice(KOTA),
                                   "country": "Indonesia", "start_date": mulai_t.isoformat(),
                                   "end_date": (mulai_t + timedelta(days=3)).isoformat(),
                                   "job_family": rt.choice(BIDANG), "code_subholding": "ABR"})

        pilihan = PELATIHAN_WAJIB + r.sample(PELATIHAN_UMUM, r.randrange(2, 6))
        for j, (nama_l, jenis) in enumerate(pilihan):
            rl = _rng("learnings-snh", nip, j)
            if jenis != "Penjenjangan" and rl.random() < 0.25:
                continue
            selesai = rl.random() < 0.85
            dt_sel = _tanggal(rl, date(2023, 1, 1), date(2026, 9, 30)) if selesai else None
            pembelajaran.append({"id_learning": f"LRN-ABR-{nip}-{j + 1}", "id_employee": nip,
                                 "learning_name": nama_l, "learning_type": jenis,
                                 "is_mandatory": jenis == "Penjenjangan",
                                 "dt_completion": dt_sel.isoformat() if dt_sel else None,
                                 "dt_expiry": (dt_sel + timedelta(days=730)).isoformat() if dt_sel and jenis == "Penjenjangan" else None,
                                 "score": round(rl.uniform(70, 95), 1) if dt_sel else None,
                                 "learning_hours": rl.choice([8, 16, 24, 32, 40]),
                                 "provider": rl.choice(PENYEDIA), "created_at": None, "updated_at": None})

        for j in range(r.randrange(1, 5)):
            rc = _rng("leave-snh", nip, j)
            mulai_c = _tanggal(rc, date(2024, 1, 1), date(2026, 9, 30))
            jenis_c = rc.choice(["Cuti Tahunan", "Cuti Tahunan", "Cuti Tahunan", "Cuti Besar",
                                 "Cuti Sakit", "Cuti Melahirkan"])
            hari = rc.randrange(1, 13) if jenis_c != "Cuti Melahirkan" else 90
            cuti_b.append({"id_leave_history": f"LV-ABR-{nip}-{j + 1}", "id_employee": nip,
                           "leave_type": jenis_c, "dt_leave_start": mulai_c.isoformat(),
                           "dt_leave_end": (mulai_c + timedelta(days=hari - 1)).isoformat(),
                           "leave_duration_days": hari, "leave_reason": None, "leave_status": "Disetujui",
                           "id_approver": None, "created_at": None, "updated_at": None})
        master_csv.append({"Kode Perusahaan": "ABR", "NIK": str(int(nip)),
                           "Top Talent": "Ya" if _rng("snh-tt", nip).random() < 0.035 else "Tidak"})

    # Talent Mobility: ABR sebagai perusahaan asal (seconded keluar) atau tujuan (diperbantukan masuk)
    for o in _daftar_mobilitas():
        if "ABR" not in (o["asal"], o["tujuan"]):
            continue
        asal = o["asal"] == "ABR"
        r = _rng("snh-mob", o["k"])
        tmt = o["tmt_asal"] if asal else o["tmt_pindah"]
        nip = f"9{o['k']:06d}"
        id_sistem = f"EMP-{9000 + o['k']:04d}"
        nama = o["nama"]
        email = _email(nama, "angkasabiruretail.id", r)
        area = AREA_SNH[o["k"] % 6]
        jc = r.choice(["9", "10", "11", "12", "13"])
        status = "Seconded" if asal else "Active"
        roster.append({"code_member": nip, "personel_number": nama, "email": email,
                       "status_aktif": status, "photo_blob": None, "person_grade": jc,
                       "personnel_area_text": area[0], "area_nomenklatur": area[1],
                       "name_directorate": DIREKTORAT_SNH[o["k"] % 5], "name_group": f"Group {BIDANG[o['k'] % len(BIDANG)]}",
                       "band_name": None, "code_directorate": f"D{(o['k'] % 5) + 1}", "code_division": None,
                       "code_group": f"G{(o['k'] % 20) + 1:02d}", "code_subholding": "ABR",
                       "birthplace": o["kota"], "date_of_birth": o["lahir"].isoformat(),
                       "division": None, "education_level": None,
                       "gender_text": "Male" if o["gender"] == "L" else "Female",
                       "home_address": f"Jl. {r.choice(BELAKANG)} No. {r.randrange(1, 150)}"})
        profil.append({"id_employee": id_sistem, "old_nip": nip, "new_nip": _digit(r, 8),
                       "full_name": nama, "name_alias": nama.split()[0],
                       "academic_title": r.choice(GELAR), "corporate_email": email,
                       "employment_status": status, "photo_blob": None, "leave_type": None,
                       "created_at": None, "updated_at": None})
        rinci.append({"id_employee": id_sistem, "employee_name": nama, "id_nik": o["id_nik"],
                      "id_npwp": o["id_npwp"], "birth_place": o["kota"], "dt_birth": o["lahir"].isoformat(),
                      "dt_start_work": tmt.isoformat(), "dt_retirement": _pensiun(o["lahir"], 56).isoformat(),
                      "dt_appointed_employee": tmt.isoformat(), "dt_grade_start": tmt.isoformat(),
                      "employment_type": "PKWTT" if asal else "Talent Mobility",
                      "job_class": jc, "gender": "Male" if o["gender"] == "L" else "Female",
                      "mobile_phone": "+62" + _ponsel(r)[1:], "corporate_email": email,
                      "blood_type": r.choice(["A", "B", "AB", "O"]), "ethnicity": None,
                      "home_phone": None})
        alamat_b.append({"id_employee": id_sistem, "old_nip": nip, "employee_name": nama,
                         "address_type": "alamat_tetap",
                         "street_address": f"Jl. {r.choice(BELAKANG)} No. {r.randrange(1, 150)}",
                         "city": o["kota"], "district": None, "province": PROVINSI[o["kota"]],
                         "postal_code": _digit(r, 5), "country": "Indonesia",
                         "geo_latitude": None, "geo_longitude": None, "created_at": None, "updated_at": None})
        kontrak.append({"id_contract": f"CT-{9000 + o['k']:04d}", "id_employee": id_sistem, "old_nip": nip,
                        "employee_name": nama, "corporate_email": email,
                        "contract_number": f"KTR/{tmt.year}/{_digit(r, 4)}",
                        "contract_type": "pkwtt", "contract_status": "active",
                        "dt_contract_start": tmt.isoformat(), "dt_contract_end": None,
                        "dt_probation_start": tmt.isoformat(),
                        "dt_probation_end": (tmt + timedelta(days=60)).isoformat(),
                        "contract_renewal_count": 0, "created_at": None, "updated_at": None})
        p = posisi[r.randrange(len(posisi))]
        riwayat.append({"id": str(len(riwayat) + 1), "nik": str(int(nip)), "name": nama,
                        "position_code": p["code_position"], "position_name": p["name_position"],
                        "grade_name": p["grade_min"], "band_name": None,
                        "area_name": area[1], "directorate": DIREKTORAT_SNH[o["k"] % 5],
                        "division_name": f"Divisi {BIDANG[o['k'] % len(BIDANG)]}",
                        "job_family": BIDANG[o["k"] % len(BIDANG)],
                        "is_current": "0" if asal else "1",
                        "start_date": tmt.isoformat(),
                        "end_date": o["tmt_pindah"].isoformat() if asal else None,
                        "perusahaan": "PT. Angkasa Biru Retail", "achievement": None,
                        "desc_tugas_kewenangan": None, "code_subholding": "ABR"})
        master_csv.append({"Kode Perusahaan": "ABR", "NIK": str(int(nip)), "Top Talent": "Tidak"})

    data["employee-profile"] = profil
    data["employee-personal-details"] = rinci
    data["employees"] = roster
    data["employee-address"] = alamat_b
    data["employee_addresses"] = list(alamat_b)    # duplikat bergaya underscore: cermin employee-address
    data["employee-contracts"] = kontrak
    data["employee_contracts"] = list(kontrak)     # duplikat bergaya underscore: cermin employee-contracts
    data["spouses"], data["childrens"] = pasangan, anak
    data["educations"], data["certificates"] = pendidikan, sertifikat
    data["position_histories"] = riwayat
    data["performances"] = kinerja
    data["hukdis"] = hukdis
    data["assessment_results"], data["assessment_result_by_competences"] = asesmen, asesmen_anak
    data["trainings"], data["learnings"] = pelatihan_lama, pembelajaran
    data["leave-histories"] = cuti_b
    data["employee-assignment-histories"] = []
    for i in range(30):
        r = _rng("snh-asg", i)
        nip = semua_nip[r.randrange(len(semua_nip))]
        v = varian[r.randrange(len(varian))]
        mulai_a = _tanggal(r, date(2024, 6, 1), date(2026, 6, 30))
        data["employee-assignment-histories"].append({
            "id_assignment_history": f"ASG-{i + 1:04d}", "id_employee": nip,
            "assignment_name": r.choice(["Pelaksana Tugas (PLT)", "Pejabat Pengganti Sementara (PGS)", "Pelaksana Harian (PLH)"]),
            "assignment_position": v["position_variant_name"], "code_positions": v["id_position_variant"],
            "assignment_letter_number": f"SK-ABR-{_digit(r, 4)}/{mulai_a.year}",
            "assignment_letter_filename": None, "assignment_letter_mime_type": None, "has_file": False,
            "dt_assignment_start": mulai_a.isoformat(),
            "dt_assignment_end": (mulai_a + timedelta(days=120)).isoformat(),
            "assignment_duration_months": 4, "description": None, "created_at": None, "updated_at": None})
    data["company-document"] = [{
        "id_company_document": 1, "fk_company_id": "1", "document_type": "Akta Pendirian",
        "document_number": "AHU-0012345.AH.01.01", "dt_document": "1962-08-17",
        "document_filename": None, "document_mime_type": None, "has_file": False,
        "created_at": None, "updated_at": None}]
    data["position-documents"] = [{
        "id_position_document": i + 1, "fk_position_variant_id": v["id_position_variant"],
        "document_type": "SK Penetapan Posisi", "document_number": f"SK-POS-{i + 1:04d}/2024",
        "dt_document": "2024-01-15", "document_filename": None, "document_mime_type": None,
        "has_file": False, "created_at": None, "updated_at": None}
        for i, v in enumerate(varian[:40])]
    data["org-unit-documents"] = [{"id_org_unit_document": 1, "fk_org_unit_id": "1",
                                   "establishment_decree_number": "SK-001/1962",
                                   "establishment_decree_filename": None, "establishment_decree_mime_type": None,
                                   "has_file": False, "created_at": None, "updated_at": None}]
    # jaminan placeholder ABR: identitas berkunci id sistem, riwayat berkunci NIK tanpa nol depan
    _gender = {b["id_employee"]: b.get("gender") for b in rinci}
    _punya_riwayat = {b["nik"] for b in riwayat}
    for _p in profil:
        assert _gender.get(_p["id_employee"]), f"angkasabiruretail: {_p['old_nip']} tanpa jenis kelamin"
        assert str(int(_p["old_nip"])) in _punya_riwayat, f"angkasabiruretail: {_p['old_nip']} tanpa riwayat posisi"
    data["_master_csv"] = master_csv
    return data


# ===================================================================== Angkasa Biru LMS
def bangun_lms() -> dict:
    """Sistem LMS grup (katalog BRD 4.4: sumber learning agility = LMS, bukan HRIS per perusahaan).
    Satu endpoint lintas perusahaan: setiap baris membawa company_code (AB/ABR/ABD) dan id pegawai
    pada sistem perusahaan itu (AB: new_nip, ABR: NIP lama, ABD: id_employee). Roster diambil dari
    generator ketiga perusahaan supaya selalu konsisten (deterministik, seed sama)."""
    roster = []
    for kode, baris, kunci in (("AB", bangun_angkasabiru()["employee_profile"], "new_nip"),
                               ("ABR", bangun_angkasabiruretail()["employee-profile"], "old_nip"),
                               ("ABD", bangun_abdestination()["employee_profiles"], "id_employee")):
        roster += [(kode, p[kunci]) for p in baris]
    hasil = []
    for kode, nik in roster:
        for a_ in _agility(nik):
            a_["id_assessment"] = f"LA-{kode}-{nik}-{a_['assessment_period']}"
            a_["company_code"] = kode
            hasil.append(a_)
    return {"learning_agility_assessments": hasil}


# ===================================================================== Angkasa Biru TMS
# (sumber aspirasi, peluang pegawai punya baris dari sumber itu, tambahan peluang bagi top talent)
SUMBER_ASPIRASI = [("individual", 0.70, 0.0), ("supervisor", 0.45, 0.30),
                   ("job_holder", 0.25, 0.30), ("unit", 0.20, 0.35)]
CATATAN_ASPIRASI = ["Sesuai latar belakang pendidikan dan pengalaman kerja.",
                    "Bersedia ditempatkan di seluruh wilayah kerja.",
                    "Perlu penguatan kompetensi kepemimpinan terlebih dahulu.",
                    "Diproyeksikan siap dalam satu sampai dua tahun.",
                    "Selaras dengan rencana pengembangan karier.",
                    "Disarankan mengikuti program pengembangan talenta."]


def bangun_tms() -> dict:
    """Sistem talenta grup, Talent Management System (katalog BRD 5.1: career_aspiration). Satu endpoint
    lintas perusahaan seperti LMS: setiap baris membawa company_code (AB/ABR/ABD), id pegawai pada sistem
    perusahaan itu, dan posisi serta job family target dari master posisi perusahaan yang sama.
    Aspirasi datang dari empat sumber (individual, supervisor, job_holder, unit), paling banyak satu baris
    per pegawai per sumber; top talent lebih sering diaspirasikan atasan, pemegang jabatan, dan unit."""
    hasil = []
    for kode, data, profil, kunci, master, kunci_posisi, kunci_jf in (
            ("AB", bangun_angkasabiru(), "employee_profile", "new_nip",
             "position_master", "id_position_master", "id_job_family"),
            ("ABR", bangun_angkasabiruretail(), "employee-profile", "old_nip",
             "positions", "code_position", "code_job_family"),
            ("ABD", bangun_abdestination(), "employee_profiles", "id_employee",
             "position_masters", "id_position_master", "id_job_family")):
        posisi = [(p[kunci_posisi], p[kunci_jf]) for p in data[master]]
        top_talent = {b["NIK"] for b in data["_master_csv"] if b["Top Talent"] == "Ya"}
        for pgw in data[profil]:
            nik = pgw[kunci]
            r = _rng("tms", kode, nik)
            calon = r.sample(range(len(posisi)), 2)             # dua calon posisi target berbeda
            # NIK pada master data ABR tidak membawa nol di depan
            talenta = (str(int(nik)) if kode == "ABR" else nik) in top_talent
            urut = 0
            for sumber, peluang, tambahan in SUMBER_ASPIRASI:
                if r.random() >= min(0.95, peluang + (tambahan if talenta else 0)):
                    continue
                id_posisi, id_jf = posisi[calon[0] if r.random() < 0.75 else calon[1]]
                if sumber == "individual" and r.random() < 0.10:
                    id_posisi = None                            # hanya menyebut job family
                urut += 1
                hasil.append({"id_aspiration": f"ASP-{kode}-{nik}-{urut}", "company_code": kode,
                              "id_employee": nik, "aspiration_source": sumber,
                              "id_target_position": id_posisi, "id_target_job_family": id_jf,
                              "dt_aspiration": _tanggal(r, date(2025, 7, 1), date(2026, 9, 30)).isoformat(),
                              "aspiration_notes": r.choice(CATATAN_ASPIRASI) if r.random() < 0.15 else None})
    return {"career_aspirations": hasil}


def _jamin_lengkap(profil, kunci, identifikasi, kunci_id, riwayat, kunci_riwayat, sumber):
    """Jaminan placeholder (16 Nov 2026): setiap pegawai punya jenis kelamin dan >= 1 riwayat posisi,
    sehingga tidak ada status 'tidak diketahui' di hilir. Gagal keras bila generator melanggarnya."""
    gender = {b[kunci_id]: b.get("gender") for b in identifikasi}
    punya_riwayat = {b[kunci_riwayat] for b in riwayat}
    for pgw in profil:
        nik = pgw[kunci]
        assert gender.get(nik), f"{sumber}: {nik} tanpa jenis kelamin"
        assert nik in punya_riwayat, f"{sumber}: {nik} tanpa riwayat posisi"


def bangun(sumber: str, _folder_sample=None) -> dict:
    data = bangun_angkasabiru() if sumber == "angkasabiru" else \
        bangun_angkasabiruretail() if sumber == "angkasabiruretail" else \
        bangun_abdestination() if sumber == "abdestination" else \
        bangun_lms() if sumber == "lms" else \
        bangun_tms() if sumber == "tms" else None
    if data is None:
        raise ValueError(f"Sumber mock tidak dikenal: {sumber}")
    return {k: v for k, v in data.items() if not k.startswith("_")}


# --------------------------------------------------------------------- penulisan fixture + CSV referensi
def _tulis_csv(path: Path, baris, kolom):
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(fp, fieldnames=kolom)
        w.writeheader()
        w.writerows(baris)
    print(f"{path}: {len(baris)} baris")


def main():
    ap = argparse.ArgumentParser(description="Tulis fixture sample dan CSV referensi sintetis")
    ap.add_argument("--sample", help="folder data/sample")
    ap.add_argument("--referensi", help="folder data/refrence")
    arg = ap.parse_args()
    data_ap, data_snh, data_abd = bangun_angkasabiru(), bangun_angkasabiruretail(), bangun_abdestination()
    if arg.sample:
        for sumber, data in (("angkasabiru", data_ap), ("angkasabiruretail", data_snh), ("abdestination", data_abd),
                             ("lms", bangun_lms()), ("tms", bangun_tms())):
            folder = Path(arg.sample) / sumber
            folder.mkdir(parents=True, exist_ok=True)
            for nama, baris in data.items():
                if nama.startswith("_"):
                    continue
                json.dump(baris, open(folder / f"{nama}.json", "w"), ensure_ascii=False)
            print(f"{folder}: {sum(1 for k in data if not k.startswith('_'))} fixture")
    if arg.referensi:
        folder = Path(arg.referensi)
        _tulis_csv(folder / "Data Tanggal Lahir Angkasa Biru.csv", data_ap["_tmt_csv"],
                   ["new_nip", "tanggal_lahir", "tmt_karyawan"])
        _tulis_csv(folder / "Data Pegawai 08092026 - Nominatif.csv", data_ap["_nominatif_csv"],
                   ["nik_baru", "nama_jabatan", "unit", "area", "direktorat"])
        _tulis_csv(folder / "master_data - emp.csv", data_ap["_master_csv"] + data_snh["_master_csv"] + data_abd["_master_csv"],
                   ["Kode Perusahaan", "NIK", "Top Talent"])




# ===================================================================== Angkasa Biru Destination (HRIS ABD)
JUMLAH_ABD = 600

DESTINASI = [("D01", "Kawasan Candi Prambanan"), ("D02", "Kawasan Candi Borobudur"),
             ("D03", "Kawasan Ratu Boko"), ("D04", "Teater Pentas Ramayana"),
             ("D05", "Kawasan Wisata Nusa Dua"), ("D06", "Kantor Pusat Destinasi")]


def bangun_abdestination() -> dict:
    """Sumber ketiga: destination management. API HRIS Angkasa Biru Destination: field sudah memakai nama
    katalog (id_employee, dt_*, fk_*) dan nilai yang sudah baku (L/P, PKWTT, aktif, Cuti), sehingga
    pemetaan silver tipis. Usia pensiun 56 tahun. Data learning agility + competency assessment
    tidak ada di koleksi Postman -> dilengkapi mock (konsisten dengan sumber lain)."""
    data = {}
    data["company_types"] = [{"id_company_type": 1, "company_type_name": "Holding"},
                             {"id_company_type": 2, "company_type_name": "Member"}]
    data["companies"] = [{"id_company": "1", "company_name": "PT Angkasa Biru Destination",
                          "fk_company_type_id": 2, "company_type": "Member", "dt_establishment": "1980-07-15",
                          "address": "Jl. Raya Prambanan", "city": "Sleman", "province": "DI Yogyakarta",
                          "postal_code": "55571", "email": "corsec@angkasabirudestinasi.id",
                          "phone": "0274-496401", "website": "https://angkasabirudestinasi.id"}]
    data["company_addresses"] = [{"id_company_address": 1, "fk_company_id": "1",
                                  "street_address": "Jl. Raya Prambanan", "sub_district": "Bokoharjo",
                                  "district": "Prambanan", "city": "Sleman", "province": "DI Yogyakarta",
                                  "postal_code": "55571"}]
    data["company_documents"] = [{"id_company_document": 1, "fk_company_id": "1",
                                  "document_type": "Akta Pendirian", "document_number": "AHU-0067890.AH.01.01",
                                  "dt_document": "1980-07-15"}]
    data["org_unit_types"] = [{"id_org_unit_type": i + 1, "org_unit_type_name": n}
                              for i, n in enumerate(["Direktorat", "Divisi", "Departemen", "Unit Kawasan"])]
    data["bands"] = [{"id_band": f"ABD-BAND-{i}", "band_name": f"Band {i}", "band_sequence": i,
                      "band_category": kat, "job_class_min": lo, "job_class_max": hi}
                     for i, (kat, lo, hi) in enumerate([("Executive", 17, 23), ("Senior Managerial", 14, 16),
                                                        ("Managerial", 12, 13), ("Operational", 7, 11)], start=1)]
    data["job_families"] = [{"id_job_family": f"DJF{i + 1:02d}", "job_family_name": b,
                             "job_family_description": f"Rumpun jabatan {b}"} for i, b in enumerate(BIDANG)]
    data["job_functions"] = [{"id_job_function": f"DJFN{i + 1:02d}", "fk_job_family_id": jf["id_job_family"],
                              "job_function_name": f"Fungsi {jf['job_family_name']}",
                              "job_function_type": "Fungsional", "job_function_description": None}
                             for i, jf in enumerate(data["job_families"])]
    data["position_types"] = [{"id_position_type": "DPT1", "position_type_name": "Struktural"},
                              {"id_position_type": "DPT2", "position_type_name": "Fungsional"},
                              {"id_position_type": "DPT3", "position_type_name": "Pelaksana"}]

    # unit organisasi: pohon 3 level (puncak id = induk)
    units = [{"id_org_unit": "1", "id_parent_org_unit": "1", "org_level": 1,
              "org_unit_name": "PT Angkasa Biru Destination", "fk_id_company": "1",
              "fk_org_unit_type_id": 1, "cost_center": "D0001"}]
    nid = 2
    for kode, nama in DESTINASI:
        induk = str(nid)
        units.append({"id_org_unit": induk, "id_parent_org_unit": "1", "org_level": 2,
                      "org_unit_name": f"Divisi {nama}", "fk_id_company": "1",
                      "fk_org_unit_type_id": 2, "cost_center": f"D{nid:04d}"})
        nid += 1
        for b in range(4):
            units.append({"id_org_unit": str(nid), "id_parent_org_unit": induk, "org_level": 3,
                          "org_unit_name": f"Departemen {BIDANG[(nid + b) % len(BIDANG)]} {kode}",
                          "fk_id_company": "1", "fk_org_unit_type_id": 3, "cost_center": f"D{nid:04d}"})
            nid += 1
    data["org_units"] = units
    data["org_unit_documents"] = [{"id_org_unit_document": 1, "fk_org_unit_id": "1",
                                   "establishment_decree_number": "SK-ORG-001/1980", "has_file": False}]
    unit_bawah = [u for u in units if u["org_level"] == 3]

    posisi, varian, kompetensi_posisi, dok_posisi = [], [], [], []
    for i in range(150):
        r = _rng("abd-pos", i)
        kode = f"PD{i + 1:04d}"
        nama = f"{FUNGSI_POSISI[i % len(FUNGSI_POSISI)]} {BIDANG[i % len(BIDANG)]} {DESTINASI[i % 6][0]}"
        jc = r.choice([7, 8, 9, 10, 10, 11, 12, 13, 14, 15, 17])
        posisi.append({"id_position_master": kode, "position_master_name": nama,
                       "fk_position_type_id": data["position_types"][i % 3]["id_position_type"],
                       "id_grade": str(jc), "id_job_family": data["job_families"][i % len(BIDANG)]["id_job_family"],
                       "id_job_function": data["job_functions"][i % len(BIDANG)]["id_job_function"],
                       "active_status": "1"})
        varian.append({"id_position_variant": kode, "fk_position_master_id": kode,
                       "position_variant_name": nama, "fk_org_unit_id": unit_bawah[i % len(unit_bawah)]["id_org_unit"],
                       "job_class": str(jc), "max_active_employee": r.choice([1, 2, 5, 15]),
                       "is_job_assignment": False, "dt_active": "2024-01-01", "dt_inactive": None})
        for k_idx in r.sample(range(len(KOMPETENSI)), 4):
            nama_k, kat = KOMPETENSI[k_idx]
            kompetensi_posisi.append({"id_position_master": kode, "id_competency": f"K{k_idx + 1:02d}",
                                      "competency_name": KOMPETENSI_BAKU[nama_k],
                                      "competency_category": KATEGORI_KOMPETENSI[kat],
                                      "required_level": str(r.randrange(1, 6))})
        if i < 30:
            dok_posisi.append({"id_position_document": i + 1, "fk_position_variant_id": kode,
                               "document_type": "SK Penetapan Posisi",
                               "document_number": f"SK-POS-D{i + 1:04d}/2024", "dt_document": "2024-02-01",
                               "has_file": False})
    data["position_masters"], data["position_variants"] = posisi, varian
    data["position_competency_requirements"] = kompetensi_posisi
    data["position_documents"] = dok_posisi

    profil, identifikasi, alamat, keluarga, pendidikan, kontrak = [], [], [], [], [], []
    riwayat, penugasan_skd, kinerja, pembelajaran, cuti, comp = [], [], [], [], [], []
    master_csv = []
    for i in range(JUMLAH_ABD):
        r = _rng("abd-peg", i)
        nik = f"ABD{i + 1:05d}"
        nama = _nama(r)
        aktif = r.random() >= 0.04
        # usia pensiun 56: pegawai aktif lahir >= 1971
        lahir = _tanggal(r, date(1971 if aktif else 1966, 1, 1), date(2003, 12, 28))
        tmt = _tanggal(r, date(max(1992, lahir.year + 18), 1, 1), date(2026, 6, 30))
        email = _email(nama, "angkasabirudestinasi.id", r)
        kota = r.choice(KOTA)
        profil.append({"id_employee": nik, "new_nip": nik, "old_nip": nik, "full_name": nama,
                       "academic_title": r.choice(GELAR), "corporate_email": email,
                       "employment_status": "aktif" if aktif else "tidak aktif", "photo_blob": None,
                       "area_name": DESTINASI[i % 6][1], "directorate_name": f"Direktorat {BIDANG[i % 5]}",
                       "org_group_name": f"Group {BIDANG[i % len(BIDANG)]}", "band_name": None})
        identifikasi.append({"id_employee": nik, "id_nik": _digit(r, 16),
                             "id_npwp": _digit(r, 15), "birth_place": kota,
                             "dt_birth": lahir.isoformat(), "dt_start_work": tmt.isoformat(),
                             "dt_retirement": _pensiun(lahir, 56).isoformat(),
                             "dt_appointed_employee": tmt.isoformat(),
                             "dt_grade_start": _tanggal(r, tmt, date(2026, 6, 30)).isoformat(),
                             "employment_type": r.choice(["PKWTT", "PKWTT", "PKWT"]),
                             "job_class": str(r.choice([7, 8, 9, 10, 10, 11, 12, 13, 14, 15, 17])),
                             "gender": r.choice(["L", "P"]), "mobile_phone": _ponsel(r),
                             "corporate_email": email})
        alamat.append({"id_employee": nik, "address_type": "Alamat Tetap",
                       "street_address": f"Jl. {r.choice(BELAKANG)} No. {r.randrange(1, 150)}",
                       "city": kota, "district": None, "province": PROVINSI[kota], "postal_code": _digit(r, 5)})
        for j in range(r.randrange(0, 4)):
            rk = _rng("abd-kel", nik, j)
            keluarga.append({"id_family_member": f"FM-{nik}-{j + 1}", "id_employee": nik,
                             "full_name": _nama(rk), "relationship_type": "Pasangan" if j == 0 else "Anak",
                             "gender": rk.choice(["L", "P"]),
                             "dt_birth": _tanggal(rk, date(1972, 1, 1), date(2022, 12, 28)).isoformat(),
                             "birth_place": rk.choice(KOTA), "dt_marriage": None, "id_number": None,
                             "id_type": None, "marital_status": None, "nationality": "Indonesia"})
        for j in range(r.randrange(1, 3)):
            re_ = _rng("abd-edu", nik, j)
            pendidikan.append({"id_education_history": f"EDU-{nik}-{j + 1}", "id_employee": nik,
                               "education_degree_type": re_.choice(["SLTA", "D3", "S1", "S1", "S2"]),
                               "education_level_code": None, "institution_name": re_.choice(UNIVERSITAS),
                               "major": re_.choice(JURUSAN), "faculty": None,
                               "dt_start": None, "dt_end": None,
                               "final_score": round(re_.uniform(2.8, 3.9), 2),
                               "institution_country": "Indonesia", "certificate_number": None})
        mulai_k = _tanggal(r, tmt, date(2026, 6, 30))
        kontrak.append({"id_contract": f"CT-{nik}", "id_employee": nik,
                        "contract_number": f"KTR-D/{mulai_k.year}/{_digit(r, 4)}",
                        "contract_type": r.choice(["PKWTT", "PKWTT", "PKWT"]),
                        "contract_status": "aktif" if aktif else "berakhir",
                        "dt_contract_start": mulai_k.isoformat(),
                        "dt_contract_end": (mulai_k + timedelta(days=730)).isoformat() if r.random() < 0.3 else None,
                        "dt_probation_start": mulai_k.isoformat(),
                        "dt_probation_end": (mulai_k + timedelta(days=r.choice([45, 60, 75]))).isoformat(),
                        "contract_renewal_count": r.randrange(0, 3)})
        n_riwayat = r.randrange(1, 4)
        mulai_p = tmt
        for j in range(n_riwayat):
            rp = _rng("abd-pos-hist", nik, j)
            v = varian[rp.randrange(len(varian))]
            riwayat.append({"id_position_history": str(len(riwayat) + 1), "new_nip": nik,
                            "fk_position_variant_id": v["id_position_variant"],
                            "position_name": v["position_variant_name"], "position_type": None,
                            "job_class": v["job_class"], "org_unit_name": None,
                            "company_name": "PT Angkasa Biru Destination",
                            "dt_position_start": mulai_p.isoformat(), "dt_position_end": None})
            mulai_p = _tanggal(rp, mulai_p, date(2026, 6, 1)) if mulai_p < date(2026, 6, 1) else mulai_p
        if r.random() < 0.05:
            ra = _rng("abd-asg", nik)
            v = varian[ra.randrange(len(varian))]
            mulai_a = _tanggal(ra, date(2024, 6, 1), date(2026, 6, 30))
            penugasan_skd.append({"id_assignment_history": f"ASG-D{len(penugasan_skd) + 1:04d}",
                                  "id_employee": nik,
                                  "assignment_name": ra.choice(["Pelaksana Tugas (PLT)",
                                                                "Pejabat Pengganti Sementara (PGS)",
                                                                "Pelaksana Harian (PLH)"]),
                                  "assignment_position": v["position_variant_name"],
                                  "assignment_letter_number": f"SK-D-{_digit(ra, 4)}/{mulai_a.year}",
                                  "dt_assignment_start": mulai_a.isoformat(),
                                  "dt_assignment_end": (mulai_a + timedelta(days=120)).isoformat(),
                                  "assignment_duration_months": 4, "description": None})
        for tahun in (2023, 2024, 2025):
            if tmt.year > tahun:
                continue
            rp = _rng("abd-perf", nik, tahun)
            kinerja.append({"id_performance_history": f"PERF-{nik}-{tahun}", "id_employee": nik,
                            "period_year": tahun, "period_label": f"Tahunan {tahun}",
                            "performance_score": round(rp.uniform(60, 99), 1),
                            "performance_rating": rp.choices(["Partially Successful", "Successful",
                                                              "Excellence", "Outstanding"],
                                                             weights=[10, 60, 20, 10])[0],
                            "pct_kpi_achievement": round(rp.uniform(70, 120), 1)})
        pilihan = PELATIHAN_WAJIB + r.sample(PELATIHAN_UMUM, r.randrange(2, 6))
        for j, (nama_l, jenis) in enumerate(pilihan):
            rl = _rng("abd-learn", nik, j)
            selesai = rl.random() < 0.85
            dt_sel = _tanggal(rl, date(2023, 1, 1), date(2026, 9, 30)) if selesai else None
            pembelajaran.append({"id_learning": f"LRN-ABD-{nik}-{j + 1}", "id_employee": nik,
                                 "learning_name": nama_l, "learning_type": jenis,
                                 "is_mandatory": jenis == "Penjenjangan",
                                 "dt_completion": dt_sel.isoformat() if dt_sel else None,
                                 "dt_expiry": (dt_sel + timedelta(days=730)).isoformat()
                                              if dt_sel and jenis == "Penjenjangan" else None,
                                 "score": round(rl.uniform(70, 95), 1) if dt_sel else None,
                                 "learning_hours": rl.choice([8, 16, 24, 32, 40]),
                                 "provider": rl.choice(PENYEDIA)})
        for j in range(r.randrange(1, 5)):
            rc = _rng("abd-cuti", nik, j)
            mulai_c = _tanggal(rc, date(2025, 1, 1), date(2026, 9, 30))
            hari = rc.randrange(1, 13)
            cuti.append({"id_leave_history": f"LV-ABD-{nik}-{j + 1}", "id_employee": nik,
                         "leave_type": rc.choice(["Cuti", "Cuti", "Cuti", "Izin"]),
                         "dt_leave_start": mulai_c.isoformat(),
                         "dt_leave_end": (mulai_c + timedelta(days=hari - 1)).isoformat(),
                         "leave_duration_days": hari, "leave_reason": None,
                         "leave_status": rc.choice(["Disetujui", "Disetujui", "Disetujui Atasan", "Diajukan"])})
        rj = _rng("jobfit-abd", nik)
        for periode in PERIODE:
            if periode == PERIODE[0] and rj.random() < 0.2:
                continue
            comp.append({"id_employee": nik, "assessment_period": periode,
                         "job_fit_score": round(rj.uniform(60, 95), 1),
                         "competency_gap": round(rj.uniform(-15, 10), 1),
                         "assessment_method": rj.choice(METODE_ASES),
                         "dt_assessment": _tanggal(rj, date(2025, 7, 1) if periode == PERIODE[0] else date(2026, 1, 1),
                                                   date(2025, 12, 20) if periode == PERIODE[0] else date(2026, 6, 30)).isoformat()})
        master_csv.append({"Kode Perusahaan": "ABD", "NIK": nik,
                           "Top Talent": "Ya" if _rng("abd-tt", nik).random() < 0.03 else "Tidak"})

    # Talent Mobility: ABD sebagai perusahaan asal (diperbantukan keluar) atau tujuan (masuk)
    for o in _daftar_mobilitas():
        if "ABD" not in (o["asal"], o["tujuan"]):
            continue
        asal = o["asal"] == "ABD"
        r = _rng("abd-mob", o["k"])
        tmt = o["tmt_asal"] if asal else o["tmt_pindah"]
        nik = f"ABD9{o['k']:04d}"
        nama = o["nama"]
        email = _email(nama, "angkasabirudestinasi.id", r)
        profil.append({"id_employee": nik, "new_nip": nik, "old_nip": nik, "full_name": nama,
                       "academic_title": r.choice(GELAR), "corporate_email": email,
                       "employment_status": "tidak aktif" if asal else "aktif", "photo_blob": None,
                       "area_name": DESTINASI[o["k"] % 6][1], "directorate_name": f"Direktorat {BIDANG[o['k'] % 5]}",
                       "org_group_name": f"Group {BIDANG[o['k'] % len(BIDANG)]}", "band_name": None})
        identifikasi.append({"id_employee": nik, "id_nik": o["id_nik"],
                             "id_npwp": "".join(c for c in o["id_npwp"] if c.isdigit()),
                             "birth_place": o["kota"],
                             "dt_birth": o["lahir"].isoformat(), "dt_start_work": tmt.isoformat(),
                             "dt_retirement": _pensiun(o["lahir"], 56).isoformat(),
                             "dt_appointed_employee": tmt.isoformat(),
                             "dt_grade_start": tmt.isoformat(),
                             "employment_type": "PKWTT" if asal else "Talent Mobility",
                             "job_class": str(r.choice([9, 10, 11, 12, 13])),
                             "gender": o["gender"], "mobile_phone": _ponsel(r),
                             "corporate_email": email})
        alamat.append({"id_employee": nik, "address_type": "Alamat Tetap",
                       "street_address": f"Jl. {r.choice(BELAKANG)} No. {r.randrange(1, 150)}",
                       "city": o["kota"], "district": None, "province": PROVINSI[o["kota"]],
                       "postal_code": _digit(r, 5)})
        kontrak.append({"id_contract": f"CT-{nik}", "id_employee": nik,
                        "contract_number": f"KTR-D/{tmt.year}/{_digit(r, 4)}",
                        "contract_type": "PKWTT", "contract_status": "aktif",
                        "dt_contract_start": tmt.isoformat(), "dt_contract_end": None,
                        "dt_probation_start": tmt.isoformat(),
                        "dt_probation_end": (tmt + timedelta(days=60)).isoformat(),
                        "contract_renewal_count": 0})
        v = varian[r.randrange(len(varian))]
        riwayat.append({"id_position_history": str(len(riwayat) + 1), "new_nip": nik,
                        "fk_position_variant_id": v["id_position_variant"],
                        "position_name": v["position_variant_name"], "position_type": None,
                        "job_class": v["job_class"], "org_unit_name": None,
                        "company_name": "PT Angkasa Biru Destination",
                        "dt_position_start": tmt.isoformat(),
                        "dt_position_end": o["tmt_pindah"].isoformat() if asal else None})
        master_csv.append({"Kode Perusahaan": "ABD", "NIK": nik, "Top Talent": "Tidak"})

    # secondary assignment (katalog 2.10): turunan penugasan + varian sah
    sekunder = [{"id_secondary_assignment": f"SA-{a['id_assignment_history']}", "new_nip": a["id_employee"],
                 "employee_name": None, "fk_position_variant_id": None, "position_name": a["assignment_position"],
                 "position_type": None, "job_class": None, "org_unit_name": None, "company_name": None,
                 "assignment_letter_number": a["assignment_letter_number"], "dt_assignment_letter": None,
                 "secondary_assignment_type": a["assignment_name"],
                 "dt_assignment_start": a["dt_assignment_start"], "dt_assignment_end": a["dt_assignment_end"]}
                for a in penugasan_skd]
    data["employee_profiles"] = profil
    data["employee_identifications"] = identifikasi
    data["employee_addresses"] = alamat
    data["employee_family_members"] = keluarga
    data["employee_education_histories"] = pendidikan
    data["employee_contracts"] = kontrak
    data["employee_position_histories"] = riwayat
    data["employee_secondary_assignments"] = sekunder
    data["employee_assignment_histories"] = penugasan_skd
    data["employee_performance_histories"] = kinerja
    data["performance_histories"] = list(kinerja)       # duplikat bagian Transaction (katalog 4.2)
    data["learning_histories"] = pembelajaran
    data["employee_leave_histories"] = cuti
    data["competency_assessments"] = comp               # tidak ada di koleksi Postman: dilengkapi mock
    _jamin_lengkap(profil, "new_nip", identifikasi, "id_employee", riwayat, "new_nip", "abdestination")
    data["_master_csv"] = master_csv
    return data


if __name__ == "__main__":
    main()
