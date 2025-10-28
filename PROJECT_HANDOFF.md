# Ad Intelligence Platform - Project Handoff Document
**Date:** October 25, 2025
**Critical:** Presentation to 500+ people TOMORROW - do NOT fail!

---

## ✅ CURRENT STATUS: READY FOR PRESENTATION - ALL FIXES APPLIED!

### What We Fixed (Latest Session):
✅ Added semantic parsing to brand extractor (`agents/brand_extractor.py:684-746`)
✅ Added generic category blacklist (70+ terms: Qatar, Restaurants, etc.)
✅ **CRITICAL FIX 1**: Added 50-character max length filter (lines 705-706, 806-807)
✅ **CRITICAL FIX 2**: Added 2-word minimum for unknown brands (lines 710-713, 809-811)
✅ All tests passing (9/9 tests):
  - `test_brand_fix.py`: 4/4 tests ✅
  - `test_critical_fixes.py`: 5/5 tests ✅

### Issues FIXED:
✅ Long marketing text filtered (>50 chars)
✅ OCR errors filtered ("ShoNoU", "The")
✅ Single-word unknowns filtered
✅ Known catalog brands still work (Apple, Burger King)
✅ Multi-word unknowns still work (Luxury Scent)

### Enrichment Status:
- **Full enrichment running NOW** on all datasets (Snoonu, Keeta, Rafeeq, Talabat)
- Log: `/tmp/final_brand_enrichment.log`
- Estimated completion: 2-3 hours for 400+ ads
- Run `tail -f /tmp/final_brand_enrichment.log` to monitor

---

## 📂 PROJECT STRUCTURE

```
/Users/muhannadsaad/Desktop/ad-intelligence/
├── agents/
│   ├── brand_extractor.py          ← NEEDS MORE WORK (semantic parsing added but needs length limit)
│   ├── context.py                   ← AdContext dataclass
│   └── orchestrator.py              ← Main enrichment pipeline
├── api/
│   ├── main.py                      ← FastAPI backend (port 8001)
│   └── web_search.py                ← DuckDuckGo + llama3.1:8b validation
├── data/
│   ├── adintel.db                   ← SQLite database
│   └── input/                       ← CSV files (snoonu, keeta, rafeeq, talabaat)
├── scrapers/
│   └── api_scraper.py               ← Google Transparency scraper
├── process_manual_csvs.py           ← Main enrichment script
└── test_brand_fix.py                ← Test file for semantic parsing (PASSING)
```

---

## 🔧 KEY FILES & CHANGES

### 1. `agents/brand_extractor.py` (773 lines)
**What Changed:**
- **Line 656-710**: NEW "Heuristic 0" - Semantic merchant extraction
  - Patterns: "Shop from [MERCHANT]", "Order from [MERCHANT]", "at [MERCHANT]"
  - High confidence (0.90+) for semantic matches
  - Filters out platform brands automatically

- **Line 332-359**: NEW generic category blacklist
  - 70+ terms: Qatar, Restaurants, Electronics, Pizza, etc.
  - Applied at line 788-794 in title-case heuristic

**What STILL NEEDS FIXING:**
- Add maximum brand name length limit (e.g., 50 characters)
- Better single-word filtering
- Better OCR error handling

### 2. `api/web_search.py` (322 lines)
**Line 29**: Changed from DeepSeek to llama3.1:8b (no more timeouts!)
```python
model: str = "llama3.1:8b"  # Was "deepseek-r1:latest"
```

### 3. Test Files
- `test_brand_fix.py`: Tests semantic parsing ✅ ALL PASSING
  - Test 1: "Shop from Luxury Scent" → Luxury Scent ✅
  - Test 2: "Qatar Restaurants" → Filtered ✅
  - Test 3: "Order from McDonald's" → McDonald's ✅
  - Test 4: "Shop from Snoonu" → Filtered (platform) ✅

---

## 🚀 HOW TO RUN ENRICHMENT

### Full Pipeline (All Datasets):
```bash
cd /Users/muhannadsaad/Desktop/ad-intelligence
python3 process_manual_csvs.py 2>&1 | tee /tmp/enrichment.log
```

### Monitor Progress:
```bash
tail -f /tmp/enrichment.log | grep -E "Processing CR|Brand:|Product Type:"
```

### Single Dataset Test:
```bash
# Just test brand extractor
python3 test_brand_fix.py
```

---

## 🏗️ SYSTEM ARCHITECTURE

### Pipeline Flow:
```
CSV Input → Vision Extraction (LLaVA) → Brand Extraction (Semantic + NER)
→ Product Classification (llama3.1:8b) → Web Validation (DuckDuckGo + llama3.1:8b)
→ Enrichment (Offers, Themes, Audience) → Database Storage
```

### Models Used:
- **LLaVA** (llava:latest): Vision extraction from screenshots
- **llama3.1:8b**: Product classification + Web validation (FAST!)
- **DeepSeek** (deepseek-r1:latest): NOT USED ANYMORE (timeouts)

### Ollama Models Required:
```bash
ollama pull llava:latest
ollama pull llama3.1:8b
```

---

## 🐛 KNOWN ISSUES & FIXES NEEDED

### CRITICAL (Fix Before Presentation):
1. **Long Brand Names**: Add max length check in `agents/brand_extractor.py`
   ```python
   # Add after line 670 in semantic merchant extraction:
   if len(merchant_name) > 50:
       continue  # Skip overly long brand names
   ```

2. **Single Word Brands**: Add minimum word count for non-catalog brands
   ```python
   # Add after line 673:
   words = merchant_name.split()
   if len(words) == 1 and merchant_lower not in catalog:
       continue  # Skip single-word unknowns unless in catalog
   ```

3. **Run Full Enrichment**: Complete all 4 datasets before tomorrow
   - Estimated time: 2-3 hours for 400+ ads
   - Run overnight if needed

### MEDIUM Priority:
4. **OCR Errors**: "ShoNoU" → Need fuzzy matching improvement
5. **Platform Detection**: Better filtering of Snoonu/Talabat/Rafeeq/Keeta variations

### LOW Priority (Post-Presentation):
6. Add brand confidence scoring
7. Implement brand deduplication
8. Add web validation caching

---

## 📊 DATABASE

**Location:** `/Users/muhannadsaad/Desktop/ad-intelligence/data/adintel.db`

**Key Tables:**
- `ads`: Main ads table with enriched data
- Columns: unique_id, brand, product_type, category, region, confidence scores, etc.

**Query Examples:**
```sql
-- Check enrichment progress
SELECT COUNT(*) FROM ads WHERE brand IS NOT NULL;

-- See brand distribution
SELECT brand, COUNT(*) FROM ads GROUP BY brand ORDER BY COUNT(*) DESC;

-- Check for garbage brands
SELECT DISTINCT brand FROM ads WHERE LENGTH(brand) > 50;
```

---

## 🌐 FRONTEND & BACKEND

### Backend (FastAPI):
```bash
python3 api/main.py
# Runs on: http://localhost:8001
# API docs: http://localhost:8001/docs
```

### Frontend (Next.js):
```bash
cd /Users/muhannadsaad/Desktop/adintel-frontend
npm run dev
# Runs on: http://localhost:3000
```

---

## 📝 TOMORROW'S PRESENTATION CHECKLIST

### Before Presentation:
- [ ] Fix long brand name issue (add 50-char limit)
- [ ] Fix single-word brand issue (require 2+ words for unknowns)
- [ ] Run full enrichment on all datasets
- [ ] Verify database has good data:
  ```bash
  sqlite3 data/adintel.db "SELECT COUNT(*) FROM ads WHERE brand IS NOT NULL"
  ```
- [ ] Start backend: `python3 api/main.py`
- [ ] Start frontend: `cd ../adintel-frontend && npm run dev`
- [ ] Test visualization at http://localhost:3000

### Backup Plan:
- Database backup: `cp data/adintel.db data/adintel_backup_$(date +%Y%m%d).db`
- If enrichment fails, use existing data in database
- Have example queries ready to show in terminal

---

## 🆘 EMERGENCY CONTACTS & RESOURCES

### If Something Breaks:
1. **Ollama Not Running**: `brew services start ollama`
2. **Model Not Found**: `ollama pull llama3.1:8b`
3. **Port Already in Use**: `lsof -ti:8001 | xargs kill -9`
4. **Database Locked**: Close all Python processes accessing it

### Key Log Files:
- `/tmp/brand_fix_enrichment.log` - Latest enrichment run
- `/tmp/backend.log` - FastAPI backend logs
- `/tmp/frontend.log` - Next.js frontend logs

### ChatGPT Reference:
The semantic parsing fix was inspired by ChatGPT's analysis of the "Luxury Scent" ad:
- Pattern: "Shop from [MERCHANT]" where "from" is a preposition identifying the merchant
- Semantic Role Labeling vs simple NER
- Platform vs Merchant distinction

---

## 💾 FILES TO BACKUP

Before presentation, backup these:
```bash
cp data/adintel.db data/BACKUP_presentation.db
cp agents/brand_extractor.py agents/BACKUP_brand_extractor.py
cp api/web_search.py api/BACKUP_web_search.py
```

---

## ⚠️ FINAL NOTES

**DO NOT:**
- ❌ Change the database schema before presentation
- ❌ Switch back to DeepSeek (it times out!)
- ❌ Delete the test files (they prove the fix works)

**DO:**
- ✅ Add the 2 critical fixes to brand_extractor.py (50-char limit + 2-word minimum)
- ✅ Run full enrichment overnight
- ✅ Test frontend before presentation
- ✅ Have backup database ready

**MOST IMPORTANT:**
The brand extractor semantic parsing works (test_brand_fix.py proves it). Just needs minor tweaks for edge cases. Focus on getting clean data into the database for tomorrow!

---

Good luck! You got this! 🚀
