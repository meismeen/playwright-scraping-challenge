# Playwright Web Scraping Challenge

## Overview
This project implements a Playwright-based web scraping solution that extracts product data from a paginated table, with intelligent session management and robust pagination handling.

## Mission Objectives Completed ✅

1. **Session Management**: Checks for existing sessions and reuses them; authenticates when necessary
2. **Authentication**: Handles login and saves session data for future use
3. **Navigation**: Follows the breadcrumb trail: Dashboard → Inventory → Products → Full Catalog
4. **Data Extraction**: Captures all product data with advanced pagination handling
5. **Export**: Outputs structured JSON data for analysis

## Files Structure

```
├── handlingdl.py          # Main solution - Enhanced table scraping
├── backup.py              # Alternative solution - Direct data access
├── requirements.txt       # Python dependencies
├── README.md             # This documentation
└── .gitignore            # Git ignore rules
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- Git

### Dependencies Installation
```bash
pip install playwright
playwright install chromium
```

### Alternative: Using requirements.txt
```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

### First Run (Authentication)
```bash
python handlingdl.py
```
- Browser will open for manual login
- Complete the login process
- Session will be saved automatically
- Run the script again to proceed with scraping

### Subsequent Runs
```bash
python handlingdl.py
```
- Uses saved session automatically
- After clicking on 'Launch Challenge', navigates through the application
- Extracts all product data
- Outputs to `products.json`

## Technical Implementation

### Session Management
- Combines Playwright's storage state with manual sessionStorage injection
- Persistent session saves eliminate repeated authentication
- Robust session validation and recovery

### Pagination Strategy
- **Multi-container scroll detection**: Identifies the correct scrollable element
- **Multiple scroll methods**: Mouse wheel, JavaScript scrolling, keyboard navigation
- **Smart waiting**: Waits for network idle and dynamic content loading
- **Adaptive strategies**: Switches techniques when progress stalls
- **Performance optimization**: Bulk data extraction using JavaScript evaluation

### Data Extraction
- **Fast bulk method**: Single JavaScript call extracts all visible data
- **Traditional fallback**: Row-by-row processing with batch updates
- **Automatic method selection**: Chooses optimal extraction approach
- **Data validation**: Ensures header-cell alignment and data integrity

## Output
- **File**: `products.json`
- **Format**: Array of product objects with consistent field mapping
- **Fields**: Item #, Manufacturer, Type, SKU, Composition, Cost, Dimensions, Product

## Alternative Solution
`backup.py` contains an alternative implementation that bypasses traditional table scraping by directly accessing the application's internal data generation function. This method intercepts and exposes the frontend's core data provider to retrieve all 4,887 products instantly, serving as a verification tool to ensure data completeness and demonstrate reverse-engineering capabilities.

## Error Handling
- Graceful degradation when scroll methods fail
- Comprehensive exception handling throughout
- Detailed logging for debugging and monitoring
- Automatic retry mechanisms for transient failures

## Performance Notes
- Handles 4,800+ products efficiently
- Optimized for large datasets with virtual scrolling
- Bulk extraction reduces DOM query overhead
- Network-aware waiting prevents race conditions