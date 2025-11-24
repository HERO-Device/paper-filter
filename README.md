# Scopus Paper Filter

A Python tool for processing and filtering Scopus paper exports with an interactive web UI.

## Features

- **Duplicate Removal**: Automatically detect and remove duplicate papers based on titles
- **Interactive UI**: Web-based interface for filtering papers
- **NLP Filters**:
  - Keyword inclusion (AND/OR logic)
  - Keyword exclusion
  - Title length filtering
  - Manual row removal
- **Swipe Review**: Tinder-style interface for quick paper review with keyboard shortcuts (Y/N)
- **Analytics**: View word frequency distributions with stop word filtering (excludes common words like "the", "and", etc.)
- **Export**: Download filtered results or save to data directory

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

Note: This uses Flask which has much simpler dependencies than Streamlit and doesn't require C++ compilation tools.

2. **Place your CSV file** in the `data/` directory:
   - The file should match the pattern `scopus_export*.csv`
   - It should have a column containing paper titles

## Usage

### Step 1: Remove Duplicates

Run the data processing script to remove duplicates:

```bash
cd processing
python data_processing.py
```

This will:
- Load your CSV file
- Automatically detect the title column
- Remove duplicate entries
- Save the processed file as `data/processed_papers.csv`

### Step 2: Launch the Filter UI

Start the Flask web server:

```bash
cd processing
python app.py
```

Then open your browser and go to: **http://localhost:5000**

The web interface will be ready to use!

## Using the Filter UI

### Sidebar Controls

1. **Include Keywords**:
   - Enter keywords (one per line) that papers should contain
   - Toggle "Require ALL keywords" for AND logic (default is OR)
   - Example: Enter "machine learning" and "neural network" to find papers about both topics

2. **Exclude Keywords**:
   - Enter keywords that should exclude papers
   - Papers containing any of these words will be removed
   - Example: Enter "review" to exclude review papers

3. **Title Length**:
   - Set minimum and maximum word counts
   - Useful for filtering out very short or very long titles

4. **Apply Filters**: Click to apply all selected filters

5. **Reset Filters**: Clear all filters and return to the full dataset

### Main Tabs

1. **Overview** 📊:
   - View filtering statistics
   - Analyze word frequency distributions (automatically excludes common stop words)
   - Identify common themes in your papers

2. **Swipe** 👆:
   - Review papers one at a time with a Tinder-style interface
   - Press **Y** (or click ✓) to keep a paper
   - Press **N** (or click ✖) to reject a paper
   - Track your progress with a visual progress bar
   - See live counts of kept vs. rejected papers
   - Export only your kept papers when done
   - Perfect for final manual curation after applying broad filters

3. **Preview Data** 📝:
   - Browse filtered papers in a table
   - Search within results
   - Manually select and remove specific papers

4. **Export** 💾:
   - Download filtered results as CSV
   - Save to the data directory for further processing

## Example Workflow

### Recommended: Filter → Swipe → Export

1. **Initial Processing**:
   ```bash
   python data_processing.py
   ```
   Output: Removes duplicates from 15,913 papers

2. **Launch UI**:
   ```bash
   python app.py
   ```
   Then open: http://localhost:5000

3. **Apply Broad Filters** (Optional but recommended):
   - Include keywords: "deep learning", "computer vision"
   - Exclude keywords: "survey", "review"
   - Min words: 5, Max words: 20
   - This reduces papers from thousands to hundreds

4. **Swipe Review**:
   - Go to the **Swipe** tab
   - Quickly review each paper title
   - Press `Y` to keep relevant papers
   - Press `N` to reject irrelevant ones
   - Download your final kept papers

5. **Alternative: Direct Export**:
   - Skip swipe and go to **Export** tab
   - Download all filtered papers as `filtered_papers.csv`

## File Structure

```
/
├── data/
│   ├── scopus_export....csv       # Your original export
│   └── processed_papers.csv       # After duplicate removal
├── processing/
│   ├── data_processing.py         # Duplicate removal script
│   ├── app.py                     # Flask web server
│   └── templates/
│       └── index.html             # Web UI
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Tips

- **Start Broad**: Begin with loose filters and gradually tighten them
- **Check Word Frequencies**: Use the Overview tab to identify common terms in your dataset
- **Iterative Filtering**: Apply filters multiple times with different criteria
- **Save Intermediate Results**: Export after each major filtering step
- **Manual Review**: Use the search function to spot-check specific terms

## Troubleshooting

**UI won't start**:
- Ensure Flask is installed: `pip install flask flask-cors`
- Check you're in the `processing/` directory
- Make sure port 5000 is not in use

**No data found**:
- Verify CSV file is in `data/` directory
- Check filename matches `scopus_export*.csv`
- Run `data_processing.py` first to create `processed_papers.csv`

**Filters not working**:
- Click "Apply Filters" after changing criteria
- Check that keywords are entered one per line
- Verify title column is correctly identified (shown in processing output)

**Installation issues**:
- If you get compilation errors with pyarrow, don't worry - it's optional
- The app works fine with just pandas, numpy, and flask

## Advanced Usage

### Custom Duplicate Detection

Modify the `remove_duplicates()` call in `data_processing.py`:

```python
# Remove duplicates based on multiple columns
processor.remove_duplicates(subset=['title', 'authors'])

# Keep the last occurrence instead of first
processor.remove_duplicates(keep='last')
```

### Programmatic Filtering

You can also filter programmatically without the UI:

```python
from data_processing import PaperProcessor

processor = PaperProcessor("../data/processed_papers.csv")
processor.load_data()

# Custom filtering
df = processor.df
filtered = df[df['title'].str.contains('deep learning', case=False)]

# Save results
filtered.to_csv("../data/custom_filtered.csv", index=False)
```

## Next Steps

After filtering, you might want to:
- Perform citation analysis
- Export to reference managers (Zotero, Mendeley)
- Create visualizations of research trends
- Extract abstracts for further NLP analysis
- Group papers by topics using clustering

## Support

If you encounter issues:
1. Check that all dependencies are installed
2. Verify your CSV file format
3. Review the console output for error messages
4. Ensure you're using Python 3.8 or higher
