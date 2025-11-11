# IPSOS Barometer Scraping - Summary

## ✅ What We Built

A complete scraping solution for the IPSOS political barometer that:

1. **Automatically detects** Flourish visualization IDs from the IPSOS barometer page
2. **Downloads** the HTML source of each visualization  
3. **Organizes** files by date in the `polls/ipsos_YYYYMM/` structure
4. **Integrates** with the existing extraction pipeline

## 📁 Files Created

```
scraping/scraping_IPSOS/
├── scrape_ipsos_barometer.py   # Main scraper script (331 lines)
├── README.md                    # Complete documentation
└── SUMMARY.md                   # This file
```

## 🎯 Key Features

### Detection Strategy
- **Problem**: Flourish visualizations are referenced as thumbnails on public.flourish.studio
- **Solution**: Extract visualization IDs and construct embed URLs for flo.uri.sh
- **Pattern**: `visualisation/(\d+)` → `https://flo.uri.sh/visualisation/{id}/embed?auto=1`

### Date Extraction
- Tries to extract publication date from HTML meta tags
- Falls back to parsing French date formats in page content
- Uses current date if extraction fails
- Generates poll ID: `ipsos_YYYYMM`

### File Naming
- First visualization: `source.html` (main/default file for extraction)
- Additional visualizations: `source_{viz_id}.html`
- Follows existing naming convention for compatibility

### Error Handling
- Dry-run mode for testing without downloading
- Continues on individual visualization failures
- Comprehensive summary output
- HTTP timeouts and retries

## 🚀 Usage Examples

### Dry Run (Test)
```bash
cd scraping/scraping_IPSOS
python scrape_ipsos_barometer.py --dry-run
```

Output:
```
🔍 Scraping IPSOS Barometer: https://www.ipsos.com/...
📥 Downloading main page...
📅 Publication date: 2025-11-07
🆔 Poll ID: ipsos_202511

🔎 Searching for Flourish visualizations...
✅ Found 3 Flourish visualization(s)
   - ID: 21670226, URL: https://flo.uri.sh/visualisation/21670226/embed?auto=1
   - ID: 21670396, URL: https://flo.uri.sh/visualisation/21670396/embed?auto=1
   - ID: 21670948, URL: https://flo.uri.sh/visualisation/21670948/embed?auto=1

📁 Would create directory: ../../polls/ipsos_202511 (dry-run mode)
```

### Actual Download
```bash
python scrape_ipsos_barometer.py
```

Creates:
```
polls/ipsos_202511/
├── source.html                 # Main visualization (21670226)
├── source_21670396.html        # Additional viz
└── source_21670948.html        # Additional viz
```

### Custom Output Directory
```bash
python scrape_ipsos_barometer.py --output-dir /custom/path
```

## 🔗 Integration with Extraction Pipeline

After scraping:

1. **Manual extraction**:
   ```bash
   cd ../../mining/mining_IPSOS
   python extract_ipsos_from_html.py ../../polls/ipsos_202511/source.html
   ```

2. **Or create a PR** - GitHub Actions will automatically:
   - Detect the new HTML file
   - Extract candidate data
   - Generate CSV files
   - Update polls.csv
   - Commit results

## 📊 Test Results (2025-11-10)

**Page scanned**: IPSOS Barometer (November 7, 2025 edition)

**Visualizations found**: 3
- 21670226 (main - will be source.html)
- 21670396 (additional)
- 21670948 (additional)

**Date extracted**: 2025-11-07
**Poll ID generated**: ipsos_202511

## 🔧 Technical Details

### Dependencies
- `requests` - HTTP client
- `beautifulsoup4` - HTML parsing
- Standard library only (no heavy dependencies)

### HTTP Headers
Includes browser-like headers to avoid blocking:
- User-Agent: Firefox on Linux
- Accept headers for HTML/XHTML
- Accept-Language: French priority

### Patterns Used
```python
# Find all visualization IDs
FLOURISH_VIZ_PATTERN = r'visualisation/(\d+)'

# Construct embed URLs
FLOURISH_EMBED_TEMPLATE = "https://flo.uri.sh/visualisation/{}/embed?auto=1"
```

### Date Formats Supported
- ISO 8601 meta tags: `2025-11-07T14:30:00Z`
- French dates: `7 novembre 2025`
- Numeric dates: `07/11/2025`

## 📝 Next Steps

1. **Run the scraper** when new IPSOS barometer polls are published
2. **Review downloaded HTML** to ensure quality
3. **Run extraction** to generate CSV files
4. **Validate dates** in polls.csv (auto-inferred from folder name)
5. **Merge data** into the main database

## 🤝 Comparison with Existing Scripts

**Inspired by**: `scripts/scrap.py` (Commission des Sondages scraper)

**Similarities**:
- Uses requests + BeautifulSoup
- Browser-like headers
- Progress output
- Error handling

**Differences**:
- No PDF handling (HTML only)
- Constructs embed URLs from IDs
- Integrated with polls/ folder structure
- Works with GitHub Actions CI/CD

## 💡 Future Improvements

- [ ] Add support for historical barometer pages
- [ ] Implement change detection (only download if new)
- [ ] Add webhook/notification support
- [ ] Support for other IPSOS poll pages
- [ ] Selenium/Playwright for JavaScript-heavy pages (if needed)

## 🐛 Known Limitations

- Requires visualizations to be embedded via Flourish IDs
- Date extraction may fail on unusual formats (falls back to current date)
- Downloads all visualizations (may include non-poll graphics)
- No deduplication check (overwrites existing files)

## 📚 Documentation

- **Detailed usage**: See `README.md` in this directory
- **Extraction docs**: See `../../mining/mining_IPSOS/README.md`
- **GitHub workflow**: See `.github/workflows/auto-extract-ipsos.yml`

## ✅ Status

**Ready to use!** The scraper is tested and functional.

**Last tested**: 2025-11-10
**Test page date**: 2025-11-07
**Status**: ✅ Working - detected 3 visualizations successfully