# IPSOS Scraper - Quick Reference

## 🚀 Quick Start

```bash
# Navigate to scraping directory
cd scraping/scraping_IPSOS

# Test (dry-run)
python scrape_ipsos_barometer.py --dry-run

# Download for real
python scrape_ipsos_barometer.py

# Custom output location
python scrape_ipsos_barometer.py --output-dir /path/to/polls
```

## 📋 What It Does

1. Scrapes https://www.ipsos.com/fr-fr/barometre-politique-ipsos-bva-la-tribune-dimanche
2. Finds Flourish visualization IDs
3. Downloads HTML source for each visualization
4. Saves to `polls/ipsos_YYYYMM/source.html`

## 📁 Output Structure

```
polls/
└── ipsos_202511/
    ├── source.html              # Main visualization (for extraction)
    ├── source_21670396.html     # Additional viz 1
    └── source_21670948.html     # Additional viz 2
```

## ⚙️ Options

| Option | Description | Example |
|--------|-------------|---------|
| `--dry-run` | Test without downloading | `python scrape_ipsos_barometer.py --dry-run` |
| `--output-dir` | Custom output directory | `python scrape_ipsos_barometer.py --output-dir ~/polls` |
| `-h, --help` | Show help | `python scrape_ipsos_barometer.py --help` |

## 🔗 Next Steps After Scraping

### Option 1: Manual Extraction
```bash
cd ../../mining/mining_IPSOS
python extract_ipsos_from_html.py ../../polls/ipsos_202511/source.html
```

### Option 2: Automated via GitHub Actions
1. Commit the new HTML files
2. Create a PR
3. GitHub Actions automatically extracts and commits CSV files

## ✅ Success Indicators

```
✅ Found 3 Flourish visualization(s)
✅ Successfully downloaded: 3
✅ Done! Files are ready for extraction
```

## ❌ Common Issues

| Issue | Solution |
|-------|----------|
| No visualizations found | Check if page structure changed |
| HTTP 403/timeout | Check internet connection |
| Date not extracted | Manual verification needed in polls.csv |

## 📊 Expected Output

```
🔍 Scraping IPSOS Barometer: https://www.ipsos.com/...
📥 Downloading main page...
📅 Publication date: 2025-11-07
🆔 Poll ID: ipsos_202511
🔎 Searching for Flourish visualizations...
✅ Found 3 Flourish visualization(s)
📥 Downloading visualization 1/3...
   ✅ Saved to: ../../polls/ipsos_202511/source.html (142.3 KB)
```

## 🔍 Debugging

```bash
# Check what URLs would be downloaded
python scrape_ipsos_barometer.py --dry-run

# Manually test a Flourish URL
curl "https://flo.uri.sh/visualisation/21670948/embed?auto=1" > test.html

# Check if page is accessible
python -c "import requests; print(requests.get('https://www.ipsos.com/fr-fr/barometre-politique-ipsos-bva-la-tribune-dimanche').status_code)"
```

## 📚 Documentation

- **Full README**: `README.md`
- **Summary**: `SUMMARY.md`
- **Extraction docs**: `../../mining/mining_IPSOS/README.md`

## 💡 Tips

- Run with `--dry-run` first to verify detection
- Check publication date (auto-extracted but verify with original)
- Only `source.html` is used by extraction script
- Additional HTML files are archived for reference
- Safe to run multiple times (overwrites files)

---

**Last Updated**: 2025-11-10
**Status**: ✅ Tested and working
