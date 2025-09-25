# ChemDataExtractor2 Dependency Removal Analysis

## Summary
Out of 26 main dependencies, **6 can be safely removed** and **7 have light usage** that could potentially be replaced with alternatives.

## ❌ DEFINITELY REMOVABLE (6 dependencies)

### 1. **boto3** + **botocore**
- **Status**: Completely unused - only test data contains S3 URLs
- **Size Impact**: Large (boto3 is ~50MB with dependencies)
- **Recommendation**: **REMOVE IMMEDIATELY**

### 2. **dawg2**
- **Status**: Completely unused
- **Purpose**: Directed Acyclic Word Graph data structure
- **Recommendation**: **REMOVE IMMEDIATELY**

### 3. **protobuf**
- **Status**: Completely unused
- **Purpose**: Protocol buffer serialization
- **Recommendation**: **REMOVE IMMEDIATELY**

### 4. **python-crfsuite**
- **Status**: Completely unused
- **Purpose**: Conditional Random Fields
- **Note**: Likely legacy from older ML models
- **Recommendation**: **REMOVE IMMEDIATELY**

### 5. **scikit-learn**
- **Status**: Completely unused (no sklearn imports found)
- **Size Impact**: Large (~50MB with dependencies)
- **Recommendation**: **REMOVE IMMEDIATELY**

### 6. **pdfminer-six**
- **Status**: Completely unused
- **Purpose**: PDF text extraction
- **Note**: Possibly unused since ChemDataExtractor focuses on HTML/XML
- **Recommendation**: **REMOVE AFTER VERIFICATION**

## ⚠️ LIGHT USAGE - REPLACEMENT CANDIDATES (7 dependencies)

### 1. **beautifulsoup4** (3 files)
- **Usage**: Only for `UnicodeDammit` encoding detection
- **Files**: text/__init__.py, scrape/pub/rsc.py, scrape/selector.py
- **Replacement**: `chardet` library (smaller, focused on encoding detection)
- **Size Saved**: ~15MB
- **Recommendation**: **REPLACE with chardet**

### 2. **python-dateutil** (1 file)
- **Usage**: Only `dateutil.parser.parse()` in scrape/fields.py
- **Replacement**: Python stdlib `datetime.fromisoformat()` for ISO dates, or remove DateTimeField entirely
- **Recommendation**: **REPLACE with stdlib or remove feature**

### 3. **appdirs** (2 files)
- **Usage**: Config/data directory location (config.py, data.py)
- **Replacement**: Platform-specific stdlib paths
- **Benefit**: Minimal - appdirs is small and useful
- **Recommendation**: **KEEP (low priority for removal)**

### 4. **cssselect** (1 file)
- **Usage**: CSS selector translation in scrape/csstranslator.py
- **Assessment**: Specialized scraping tool, probably needed
- **Recommendation**: **KEEP (used for web scraping)**

### 5. **overrides** (2 files)
- **Usage**: `@override` decorator in BERT modules
- **Replacement**: Remove decorator or use typing.override in Python 3.12+
- **Recommendation**: **REPLACE with typing.override**

### 6. **nltk** (2 files)
- **Usage**: Tokenization in CLI and corpus processing
- **Assessment**: May be essential for specific NLP tasks
- **Recommendation**: **EVALUATE - check if functionality is needed**

### 7. **scipy** (1 file)
- **Usage**: Clustering in relex/cluster.py
- **Replacement**: numpy-only clustering or remove relationship extraction clustering
- **Recommendation**: **EVALUATE - assess relationship extraction importance**

## ✅ ESSENTIAL DEPENDENCIES (10 dependencies)
These should be kept:
- **lxml** (20 files) - Core XML/HTML parsing
- **click** (11 files) - CLI framework
- **requests** (6 files) - HTTP requests
- **selenium** (6 files) - Web scraping (RSC needs this)
- **numpy** (5 files) - Numerical computing
- **tokenizers** (4 files) - BERT tokenization
- **deprecation** (4 files) - Deprecation warnings
- **transformers** (3 files) - BERT models
- **stanza** (3 files) - NLP pipeline
- **yaspin** (3 files) - Progress indicators

## SPECIALIZED DEPENDENCIES
- **tabledataextractor** (2 files) - Essential for table processing, keep

## IMPLEMENTATION PLAN

### Phase 1: Immediate Removal (Safe)
```bash
# Remove completely unused dependencies
uv remove boto3 botocore dawg2 protobuf python-crfsuite scikit-learn
```

### Phase 2: Replacements
1. **Replace beautifulsoup4 with chardet**:
   - Add `chardet>=3.0.0`
   - Update encoding detection in 3 files
   - Remove beautifulsoup4

2. **Replace python-dateutil**:
   - Assess if DateTimeField is actually used
   - Replace with stdlib datetime if needed
   - Remove python-dateutil

3. **Replace overrides**:
   - Use `typing.override` in Python 3.12+
   - Remove overrides dependency

### Phase 3: Evaluation (Require testing)
1. **pdfminer-six**: Verify no PDF processing needs
2. **nltk**: Check if tokenization can be replaced
3. **scipy**: Evaluate relationship extraction clustering usage

## ESTIMATED SIZE REDUCTION
- **Immediate**: ~100MB (boto3, botocore, scikit-learn)
- **With replacements**: ~120MB total
- **Final optimized size**: Reduce dependencies from 26 to ~15-17

## RISK ASSESSMENT
- **Low Risk**: boto3, botocore, dawg2, protobuf, python-crfsuite, scikit-learn
- **Medium Risk**: beautifulsoup4, python-dateutil, overrides
- **High Risk**: pdfminer-six, nltk, scipy (need careful testing)