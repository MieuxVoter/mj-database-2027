# IPSOS Barometer Scraper

This directory contains tools to scrape the IPSOS political barometer website and download Flourish visualization data.

## Overview

The IPSOS political barometer publishes regular polls using Flourish interactive visualizations embedded in their pages. This scraper:

1. **Detects** Flourish visualization embeds on the IPSOS barometer page
2. **Downloads** the HTML source of each visualization
3. **Organizes** files by date in the `polls/ipsos_YYYYMM/` structure
4. **Prepares** data for extraction using `mining/mining_IPSOS/extract_ipsos_from_html.py`

## Target Page

**IPSOS Political Barometer**: https://www.ipsos.com/fr-fr/barometre-politique-ipsos-bva-la-tribune-dimanche

## Requirements

```bash
pip install requests beautifulsoup4
```

Or use the project's requirements:
```bash
pip install -r ../../requirements_pytests.txt
```

## Usage

### Basic Usage

```bash
cd scraping/scraping_IPSOS
python scrape_ipsos_barometer.py
```

This will:
- Scrape the IPSOS barometer page
- Download all Flourish visualizations found
- Save them to `../../polls/ipsos_YYYYMM/source.html`

### Dry Run (Test Mode)

To see what would be downloaded without actually downloading:

```bash
python scrape_ipsos_barometer.py --dry-run
```

### Custom Output Directory

```bash
python scrape_ipsos_barometer.py --output-dir /path/to/polls
```

## How It Works

### 1. **Page Scraping**
The script downloads the main IPSOS barometer page and searches for Flourish embed URLs:
```
https://flo.uri.sh/visualisation/21670948/embed?auto=1
```

### 2. **Date Extraction**
Tries to extract the publication date from:
- HTML meta tags (`article:published_time`)
- Page content (French date formats)
- Falls back to current date if not found

### 3. **Poll ID Generation**
Creates a poll ID in the format `ipsos_YYYYMM` based on the publication date:
```
November 2025 → ipsos_202511
```

### 4. **Visualization Download**
Downloads each Flourish visualization's HTML source:
- Main visualization → `source.html`
- Additional visualizations → `source_{viz_id}.html`

### 5. **File Organization**
Saves files to:
```
polls/
  ipsos_202511/
    source.html          # Main Flourish visualization HTML
    source_12345.html    # Additional visualizations (if any)
```

## Output

The script provides detailed progress output:

```
🔍 Scraping IPSOS Barometer: https://www.ipsos.com/fr-fr/barometre-politique-ipsos-bva-la-tribune-dimanche

📥 Downloading main page...
📅 Publication date: 2025-11-10
🆔 Poll ID: ipsos_202511

🔎 Searching for Flourish visualizations...
✅ Found 1 Flourish visualization(s)
   - ID: 21670948, URL: https://flo.uri.sh/visualisation/21670948/embed

📁 Output directory: ../../polls/ipsos_202511

📥 Downloading visualization 1/1 (ID: 21670948)...
   ✅ Saved to: ../../polls/ipsos_202511/source.html

================================================================================
📊 SUMMARY
================================================================================
✅ Successfully downloaded: 1
❌ Failed: 0

Downloaded files:
   - ../../polls/ipsos_202511/source.html (142.3 KB)

✅ Done! Files are ready for extraction with extract_ipsos_from_html.py
```

### Skip Existing Polls

**By default, the scraper skips polls that have already been downloaded.** This prevents unnecessary re-downloads:

```bash
python scrape_ipsos_barometer.py
# Output: ⏭️ Skipping ipsos_202511: folder already exists
```

To force re-download (e.g., if IPSOS updated the data):

```bash
python scrape_ipsos_barometer.py --force
```

## Next Steps

After scraping, use the extraction script to parse the candidate data:

```bash
cd ../../mining/mining_IPSOS
python extract_ipsos_from_html.py ../../polls/ipsos_202511/source.html
```

This will:
- Read metadata from `metadata.txt` (survey dates, sample size)
- Extract candidate names and judgment distributions
- Generate CSV files (`ipsos_202511_all.csv`)
- Update `polls.csv` with metadata

## Integration with CI/CD

When you add the scraped HTML files to a PR, the GitHub Actions workflow will automatically:
1. Detect the new HTML files
2. Run the extraction script
3. Generate CSV files
4. Commit the results

See `.github/workflows/auto-extract-ipsos.yml` for details.

## Troubleshooting

### No visualizations found
- Check if the page structure has changed
- Verify the Flourish URL pattern in `FLOURISH_PATTERN`
- Use `--dry-run` to test without downloading

### Date extraction fails
- The script will fall back to current date
- Manually verify dates in `polls.csv` after extraction
- Check the page source for date formats

### HTTP errors
- Check your internet connection
- Verify the IPSOS website is accessible
- The script includes browser-like headers to avoid blocking

## Manual Workflow

1. **Scrape**: `python scrape_ipsos_barometer.py`
2. **Review**: Check `polls/ipsos_YYYYMM/source.html`
3. **Extract**: Run extraction script or create PR for auto-extraction
4. **Validate**: Check CSV output and dates
5. **Merge**: Update the database with `merge.py`

## Notes

- The script respects the target website with appropriate delays
- HTML files are large (~100-200 KB) due to embedded data
- Only downloads new visualizations (checks if folder already has CSV)
- Safe to run multiple times (won't re-download existing data)

## Support

For issues or questions:
- Check the main project README: `../../README.md`
- Review extraction documentation: `../../mining/mining_IPSOS/README.md`
- Open an issue on the GitHub repository
