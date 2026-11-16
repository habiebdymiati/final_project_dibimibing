# Diagram proses

Sumber diagram proses (Mermaid) untuk `README.md` dan dokumen resume. Render ulang setelah mengubah `.mmd`:

```bash
docker run --rm -u "$(id -u)" -v "$PWD/docs":/data minlag/mermaid-cli \
  -i /data/diagrams/<nama>.mmd -o /data/img/<nama>.png \
  -p /data/diagrams/puppeteer.json -c /data/diagrams/proses-config.json -s 2 -b white
```

`erd-silver.png` dan `erd-gold.png` adalah salinan dari ERD katalog; sumbernya dikelola di
`data_catalogue/diagrams/` (lokal): `silver-terbaru.mmd` disunting manual, `gold-efisien.mmd`
dibangkitkan dari schema gold oleh `scripts/catalogue/update_katalog_efisien.py` (fungsi `tulis_erd_gold`).
