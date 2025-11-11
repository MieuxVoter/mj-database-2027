# IPSOS Scraper Package

A modular Python package for scraping IPSOS Political Barometer data.

## Package Structure

The scraper has been refactored into a clean, modular package structure:

```
ipsos_scraper/
├── __init__.py           # Package initialization, exports main function
├── config.py             # Configuration constants (URLs, patterns, headers)
├── url_extractor.py      # Extract Flourish visualization URLs
├── date_extractor.py     # Extract dates and survey metadata
├── downloader.py         # Download visualization HTML
├── candidate_detector.py # Identify candidate voting data
├── metadata_writer.py    # Write metadata.txt files
└── scraper.py            # Main orchestration module
```

## Module Descriptions

### config.py
Contains all configuration constants:
- `BASE_URL`: IPSOS website base URL
- `BAROMETER_URL`: Political barometer page URL
- `FLOURISH_VIZ_PATTERN`: Regex pattern for finding visualizations
- `FLOURISH_EMBED_TEMPLATE`: Template for embed URLs
- `HEADERS`: HTTP headers for requests
- `MONTH_MAP`: French month name to number mapping
- `POLITICIAN_INDICATORS`: Names used for candidate detection

### url_extractor.py
**Functions:**
- `extract_flourish_urls(html_content)`: Extract all Flourish visualization URLs from page
  - Accepts string or BeautifulSoup object
  - Returns list of dicts with viz ID and URL
  - Deduplicates and sorts results

### date_extractor.py
**Functions:**
- `extract_publication_date(soup)`: Extract publication date from meta tags or French text
  - Tries ISO 8601 format first (meta tags)
  - Falls back to French date patterns (e.g., "7 novembre 2025")
  - Returns YYYY-MM-DD string

- `extract_survey_metadata(soup)`: Extract survey info from "A propos de ce sondage" section
  - Survey date range (start and end dates)
  - Sample size (number of respondents)
  - Population description
  - Returns dict with metadata

- `generate_poll_id(date)`: Generate poll ID in format `ipsos_YYYYMM`
  - Used for folder naming
  - Returns string

### downloader.py
**Functions:**
- `download_flourish_visualization(viz_url, session)`: Download visualization HTML
  - Takes requests.Session for connection reuse
  - Returns HTML string
  - Raises on HTTP errors

### candidate_detector.py
**Functions:**
- `check_if_candidate_data(html_content)`: Detect if viz contains candidate voting data
  - Searches for politician names in `_Flourish_data` JSON section
  - Distinguishes candidate polls from policy priority polls
  - Returns True if >= 3 politician names found

### metadata_writer.py
**Functions:**
- `write_metadata(output_path, ...)`: Write metadata.txt file
  - Publication date
  - Survey date range
  - Sample size
  - Population description
  - Visualization URL
  - Source URL

### scraper.py
**Main Function:**
- `scrape_ipsos_barometer(output_dir, dry_run, force)`: Main orchestration
  1. Fetches IPSOS barometer page
  2. Extracts publication date and generates poll ID
  3. Checks if poll already exists (--skip-existing by default)
  4. Identifies all Flourish visualizations
  5. Downloads only visualization with candidate data
  6. Extracts survey metadata
  7. Saves source.html and metadata.txt
  
  Returns dict with:
  - `success`: bool
  - `poll_id`: str
  - `output_path`: Path
  - `skipped`: bool
  - `message`: str

## Usage

### As a Package

```python
from ipsos_scraper import scrape_ipsos_barometer

# Basic usage
result = scrape_ipsos_barometer(output_dir="polls")

# With options
result = scrape_ipsos_barometer(
    output_dir="polls",
    dry_run=True,  # Don't actually download
    force=False    # Skip if already exists
)

# Check result
if result['success']:
    print(f"Poll {result['poll_id']} downloaded to {result['output_path']}")
else:
    print(f"Error: {result['message']}")
```

### Command Line

```bash
# Run scraper (default behavior: skip if exists)
python scrape_ipsos_barometer.py

# Dry run (see what would be done)
python scrape_ipsos_barometer.py --dry-run

# Force re-download
python scrape_ipsos_barometer.py --force

# Custom output directory
python scrape_ipsos_barometer.py --output-dir /path/to/polls
```

## Design Principles

### Separation of Concerns
Each module has a single, clear responsibility:
- Configuration is isolated in `config.py`
- URL extraction doesn't know about dates
- Date extraction doesn't know about downloads
- Candidate detection is independent of scraping logic

### Modularity
Modules can be imported and tested independently:

```python
from ipsos_scraper.url_extractor import extract_flourish_urls
from ipsos_scraper.candidate_detector import check_if_candidate_data

# Use just the URL extractor
html = "<html>...</html>"
viz_list = extract_flourish_urls(html)

# Use just the candidate detector
is_candidate_data = check_if_candidate_data(html)
```

### Maintainability
- Clear module names indicate purpose
- Comprehensive docstrings
- Type hints for better IDE support
- Single file to edit for each concern

### Testability
Each module can be unit tested independently:

```python
# Test URL extraction
def test_extract_flourish_urls():
    html = '<a href="public.flourish.studio/visualisation/12345">viz</a>'
    result = extract_flourish_urls(html)
    assert len(result) == 1
    assert result[0]['id'] == '12345'

# Test candidate detection
def test_check_if_candidate_data():
    html = '<script>_Flourish_data = {"data": [["Macron", 0.25]]}</script>'
    assert check_if_candidate_data(html) == True
```

## Migration from Monolithic Script

The original `scrape_ipsos_barometer.py` was a single 520-line file with all logic combined. This has been refactored to:

1. **Preserve functionality**: All features work identically
2. **Same CLI interface**: No changes to command-line usage
3. **Backward compatible**: Returns same result format
4. **Better organized**: 7 focused modules vs 1 large file

Old backup: `scrape_ipsos_barometer_old.py` (520 lines)
New version: `scrape_ipsos_barometer.py` (90 lines) + `ipsos_scraper/` package

## Benefits of Refactoring

### Before (Monolithic)
- 520 lines in one file
- Hard to find specific functionality
- Difficult to test individual components
- Changes affect entire file
- High cognitive load

### After (Modular)
- 7 focused modules (30-180 lines each)
- Clear organization by responsibility
- Easy to test individual modules
- Changes isolated to relevant module
- Easy to understand each piece

## Dependencies

- **requests**: HTTP requests
- **beautifulsoup4**: HTML parsing
- **Python 3.11+**: Modern type hints and features

## Error Handling

Each module handles errors appropriately:

- **url_extractor**: Returns empty list if no visualizations found
- **date_extractor**: Returns None/empty dict if parsing fails
- **downloader**: Raises requests.RequestException on HTTP errors
- **scraper**: Catches all exceptions and returns error dict

## Future Improvements

Potential enhancements:
1. Add logging module for better debugging
2. Create unit tests for each module
3. Add retry logic for network failures
4. Support multiple barometer sources
5. Add data validation module
6. Create async version for faster downloads
