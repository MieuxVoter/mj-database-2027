# GitHub Actions - Automated Workflows

This directory contains GitHub Actions workflows for automating poll data extraction and processing.

## 🤖 auto-extract-ipsos.yml

Automatically extracts IPSOS poll data when new HTML source files are added to the repository.

### Triggers

- **Pull Request**: When HTML files are added/modified in `polls/**/` directories
- **Push to main**: When HTML files are added/modified in `polls/**/` directories

### What it does

1. **Detects IPSOS files**
   - Scans for new `.html` files in the `polls/` folder
   - Filters for files containing "ipsos" in the path/name

2. **Extracts poll data**
   - Runs `mining/mining_IPSOS/extract_ipsos_from_html.py` automatically
   - Generates CSV files with candidate data
   - Adds metadata entries to `polls.csv`
   - Infers survey dates from folder names (e.g., `ipsos_202511` → 2025-11-15)

3. **Validates extracted data**
   - Runs `mining/mining_IPSOS/validate_poll.py`
   - Checks CSV structure, candidate IDs, and percentages
   - Reports validation results

4. **Commits changes**
   - Commits generated CSV files and `polls.csv` updates
   - Pushes to the PR branch automatically
   - Uses `github-actions[bot]` as author

5. **Posts PR comment** (on Pull Requests)
   - Summary of extraction results
   - Number of candidates extracted
   - polls.csv entries added
   - **Warning to verify survey dates**
   - Next steps checklist

### Example PR Comment

```markdown
# 🤖 IPSOS Poll Auto-Extraction

## Extraction Results

### 📊 Processing: `polls/ipsos_202511/source.html`
✅ **Extraction successful**

- **Candidates extracted**: 28
- **CSV file**: `polls/ipsos_202511/ipsos_202511_all.csv`
- **polls.csv entry**: `ipsos_202511,pt1,1000,2025-11-15,2025-11-15,polls/ipsos_202511,all`

⚠️ **Please verify survey dates**: `2025-11-15` to `2025-11-15`
   (Dates were inferred from folder name. Check the original IPSOS report.)

## 🔍 Validation Results

### Validating `polls/ipsos_202511/ipsos_202511_all.csv`
✅ **Validation passed**

---

## 📋 Next Steps

1. **Verify survey dates** in `polls.csv`
   - Dates are inferred from folder names (mid-month default)
   - Check the original IPSOS report for exact dates
   - Edit `polls.csv` if needed

2. **Review extracted data**
   - Check CSV files for accuracy
   - Verify candidate mappings

3. **Run merge**
   - After verifying dates, run `python merge.py` locally
   - Or wait for the merge workflow to run automatically

4. **Approve and merge** when ready ✅
```

### Workflow Steps

```mermaid
graph TD
    A[New HTML file in PR] --> B{Contains 'ipsos'?}
    B -->|Yes| C[Extract poll data]
    B -->|No| Z[Skip]
    C --> D[Validate CSV]
    D --> E[Commit changes]
    E --> F[Push to PR branch]
    F --> G[Post PR comment]
    G --> H[Wait for review]
```

### Requirements

- Python 3.11+
- No external dependencies (uses stdlib only)
- Write access to repository
- Pull request permissions

### Configuration

The workflow uses these files:
- `mining/mining_IPSOS/extract_ipsos_from_html.py` - Extraction script
- `mining/mining_IPSOS/validate_poll.py` - Validation script
- `candidates.csv` - Candidate mapping (65 candidates)
- `polls.csv` - Poll metadata database

### Permissions

```yaml
permissions:
  contents: write        # To commit and push changes
  pull-requests: write   # To post comments on PRs
```

### Usage

1. **Add IPSOS HTML source file** to a PR:
   ```bash
   mkdir -p polls/ipsos_202512
   # Download HTML from IPSOS
   cp ~/Downloads/source.html polls/ipsos_202512/
   git add polls/ipsos_202512/source.html
   git commit -m "Add IPSOS December 2025 poll source"
   git push
   ```

2. **GitHub Action runs automatically**:
   - Extracts data within ~30 seconds
   - Commits CSV files and polls.csv
   - Posts PR comment with results

3. **Review the PR comment**:
   - Check extraction summary
   - Verify survey dates (⚠️ inferred from folder name)
   - Edit `polls.csv` if dates need adjustment

4. **Approve and merge**:
   - When dates are verified
   - CSV files look correct
   - Validation passed

### Troubleshooting

#### "No IPSOS HTML files detected"
- Check that the file is in `polls/**/` directory
- Check that filename or path contains "ipsos"
- Ensure file extension is `.html`

#### "Extraction failed"
- Check the error message in the PR comment
- Common issues:
  - Candidate not in `candidates.csv` - add them first
  - HTML format changed - update extraction script
  - Invalid folder name format

#### "Validation warnings"
- Check the validation output in the PR comment
- Fix issues in the generated CSV or `polls.csv`
- Re-run by pushing another commit

### Manual Override

If the action fails, you can run manually:

```bash
# Extract
python mining/mining_IPSOS/extract_ipsos_from_html.py polls/ipsos_YYYYMM/source.html

# Validate
python mining/mining_IPSOS/validate_poll.py polls/ipsos_YYYYMM/ipsos_YYYYMM_all.csv

# Commit
git add polls/ polls.csv
git commit -m "Add IPSOS poll YYYYMM"
git push
```

### Future Enhancements

- [ ] Auto-fetch exact dates from IPSOS API (if available)
- [ ] Support for ELABE and IFOP polls
- [ ] Automatic merge.py execution
- [ ] Slack/Discord notifications
- [ ] Auto-create releases on merge to main

## See Also

- [Mining IPSOS Documentation](../mining/mining_IPSOS/README.md)
- [COMMENT_AJOUTER_UN_SONDAGE.md](../COMMENT_AJOUTER_UN_SONDAGE.md)
- [GitHub Actions Documentation](https://docs.github.com/actions)
