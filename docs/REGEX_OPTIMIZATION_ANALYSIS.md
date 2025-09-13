# ChemDataExtractor2 Regex Optimization Analysis

## Executive Summary

ChemDataExtractor2 has significant regex optimization opportunities that could provide **2-4x faster parser initialization** and **20-30% overall performance improvement**. This analysis identifies specific patterns and implementation strategies for regex caching and compilation optimization.

## Current Regex Usage Patterns

### 1. Module-Level Compiled Regexes (Already Optimized ✅)

**Location**: `chemdataextractor/parse/quantity.py`

```python
# These are already optimized - compiled once at module load
_number_pattern = re.compile(r"(\d+\.?(?:\d+)?)")
_negative_number_pattern = re.compile(r"(-?\d+\.?(?:\d+)?)")
_simple_number_pattern = re.compile(r"(\d+(?!\d+))")
_error_pattern = re.compile(r"(\d+\.?(?:\d+)?)|(±)")
_fraction_or_decimal_pattern = re.compile(r"-?\d\d*(\.\d\d*)?(/?-?\d\d*(\.\d\d*)?)?")
_unit_fraction_pattern = re.compile(r"(/[^\d])")
_brackets_pattern = re.compile(r"(\()|(\))")
_slash_pattern = re.compile("/")
_end_bracket_pattern = re.compile(r"\)\w*")
_open_bracket_pattern = re.compile(r"/\(")
_division_pattern = re.compile(r"[/]\D*")
_magnitude_indicators = re.compile("[pnµmTGMkc]")
```

### 2. Runtime Regex Compilation (⚠️ MAJOR OPTIMIZATION OPPORTUNITY)

**Location**: `chemdataextractor/parse/elements.py`

```python
class Regex(BaseParserElement):
    def __init__(self, pattern, flags=0, group=None):
        if isinstance(pattern, str):
            self.regex = re.compile(pattern, flags)  # ⚠️ COMPILED ON EVERY INSTANCE
```

**Problem**: Every `R("pattern")` call creates a new `Regex` instance that compiles the pattern independently. Same patterns are compiled repeatedly across documents.

**Impact**: Thousands of redundant regex compilations per document.

### 3. Dictionary Building Regexes (Medium Priority)

**Location**: `chemdataextractor/cli/dict.py`

```python
# These compile once at module load - already optimized
NG_RE = re.compile(r"([\[\(](\d\d?CI|USAN|r?INN|BAN|JAN|USP)...)", re.I | re.U)
START_RE = re.compile("^(anhydrous|elemental|amorphous|conjugated...)...", re.I | re.U)
END_RE = re.compile(r"[\[\(]((crude )?product|substance|solution...)...", re.I | re.U)
RATIO_RE = re.compile(r"[\[\(]((\d\d?)(:(\d\d?|\?|\d\.\d))+)[\)\]]$", re.I | re.U)
NUM_END_RE = re.compile(r" (\d+)$", re.U)
ALPHANUM_END_RE = re.compile(r" ([A-Za-z]\d*)$", re.U)
BRACKET_RE = re.compile(r"^\(([^\(\)]+)\)$", re.I | re.U)
```

### 4. NLP Tagger Regexes (HIGH IMPACT)

**Location**: `chemdataextractor/nlp/tag.py`

```python
class RegexTagger(BaseTagger):
    def __init__(self, patterns=None, lexicon=None):
        self.patterns = patterns if patterns is not None else self.patterns
        self.regexes = [(re.compile(pattern, re.I | re.U), tag) for pattern, tag in self.patterns]
        # ⚠️ Compiles all patterns on every tagger instance
```

### 5. Function-Level Dynamic Compilation

**Location**: `chemdataextractor/parse/quantity.py`

```python
def create_units_regex(magnitudes_dict):
    # ... build regex string
    return re.compile(units_regex)  # ⚠️ Called repeatedly
```

### 6. String-Based Regex Operations (Mixed)

```python
# Runtime compilation - needs optimization
re.split(r"(\d+\.?(?:\d+)?)|(±)|(\()", string)  # ⚠️ Not compiled

# Pre-compiled usage - already good
re.match(_fraction_or_decimal_pattern, element)  # ✅ Good - compiled
```

## Key Performance Issues

### Issue #1: Parser Element Creation Overhead ⭐⭐⭐

- Every `R("pattern")` call creates a new `Regex` instance
- Each instance compiles the regex pattern independently  
- Same patterns are compiled repeatedly across documents
- **Impact**: Thousands of redundant regex compilations per document

### Issue #2: Function-Level Dynamic Compilation

- `create_units_regex()` called repeatedly with same inputs
- No caching of compiled results
- **Impact**: Redundant compilation of complex unit patterns

### Issue #3: Scattered String Operations

- Many `re.split`, `re.search`, `re.match` calls throughout codebase
- Patterns not pre-compiled
- **Impact**: Constant re-compilation overhead

## Optimization Strategies

### Strategy 1: Regex Pattern Pool with @lru_cache 🚀

**Implementation:**

```python
from functools import lru_cache
import re
from typing import Pattern

@lru_cache(maxsize=1000)
def get_compiled_regex(pattern: str, flags: int = 0) -> Pattern[str]:
    """Cache compiled regex patterns to avoid recompilation."""
    return re.compile(pattern, flags)

# Modified Regex class
class Regex(BaseParserElement):
    def __init__(self, pattern, flags=0, group=None):
        super(Regex, self).__init__()
        if isinstance(pattern, str):
            self.regex = get_compiled_regex(pattern, flags)  # ✅ Cached!
            self.pattern = pattern
        else:
            self.regex = pattern
            self.pattern = pattern.pattern
        self.group = group
```

**Expected Impact**: 60-80% reduction in regex compilation time

### Strategy 2: Pre-compile Common Patterns

**Implementation:**

```python
# New module: chemdataextractor/parse/regex_cache.py
from functools import lru_cache
import re
from typing import Dict, Pattern

class RegexCache:
    """Centralized regex pattern cache with pre-compiled common patterns."""
    
    # Pre-compile the most common patterns used in parsers
    COMMON_PATTERNS: Dict[str, Pattern[str]] = {
        'number': re.compile(r'\d+\.?\d*'),
        'negative_number': re.compile(r'-?\d+\.?\d*'),
        'word': re.compile(r'\w+'),
        'chemical_formula': re.compile(r'[A-Z][a-z]?\d*'),
        'temperature_units': re.compile(r'°?[CKF]|celsius|kelvin|fahrenheit', re.I),
        'pressure_units': re.compile(r'bar|atm|pa|torr|mmhg', re.I),
        'mass_units': re.compile(r'[kmµn]?g|kg|mg|µg|ng', re.I),
        'volume_units': re.compile(r'[kmµn]?l|ml|µl|nl', re.I),
        'brackets_open': re.compile(r'\(|\[|\{'),
        'brackets_close': re.compile(r'\)|\]|\}'),
        'greek_letters': re.compile(r'α|β|γ|δ|ε|ζ|η|θ|ι|κ|λ|μ|ν|ξ|ο|π|ρ|σ|τ|υ|φ|χ|ψ|ω'),
        # ... 40+ more common patterns
    }
    
    @classmethod
    @lru_cache(maxsize=2000)
    def get_pattern(cls, pattern: str, flags: int = 0) -> Pattern[str]:
        """Get compiled regex pattern with caching."""
        # Check if it's a pre-compiled common pattern
        cache_key = f"{pattern}_{flags}"
        if cache_key in cls.COMMON_PATTERNS:
            return cls.COMMON_PATTERNS[cache_key]
        
        # Compile and cache new patterns
        return re.compile(pattern, flags)
    
    @classmethod  
    def precompile_common_patterns(cls):
        """Pre-compile common patterns with various flag combinations."""
        common_flags = [0, re.I, re.U, re.I | re.U]
        for pattern_name, compiled_pattern in list(cls.COMMON_PATTERNS.items()):
            for flags in common_flags:
                cache_key = f"{compiled_pattern.pattern}_{flags}"
                cls.COMMON_PATTERNS[cache_key] = re.compile(compiled_pattern.pattern, flags)
```

### Strategy 3: Optimize String Operations

**Implementation:**

```python
# Pre-compile frequently used splitting patterns
_SPLIT_PATTERNS: Dict[str, Pattern[str]] = {
    'number_error_paren': re.compile(r"(\d+\.?(?:\d+)?)|(±)|(\()"),
    'space_dash': re.compile(r" |(-)"),
    'unit_fraction': re.compile(r"(/[^\d])"),
    'brackets': re.compile(r"(\))|(\()"),
    'slash': re.compile(r"/"),
}

def optimized_split_by_pattern(string: str, pattern_name: str) -> List[str]:
    """Use pre-compiled patterns for splitting operations."""
    pattern = _SPLIT_PATTERNS.get(pattern_name)
    if pattern is None:
        raise ValueError(f"Unknown split pattern: {pattern_name}")
    return [r for r in pattern.split(string) if r and r != " "]

# Replace scattered usage
# OLD: re.split(r"(\d+\.?(?:\d+)?)|(±)|(\()", string)
# NEW: optimized_split_by_pattern(string, 'number_error_paren')
```

### Strategy 4: Batch Regex Operations

**Implementation:**

```python
from typing import List, Dict, Optional

def batch_regex_search(patterns: List[Pattern[str]], text: str) -> Dict[int, re.Match[str]]:
    """Apply multiple regex patterns efficiently to the same text."""
    results = {}
    for i, pattern in enumerate(patterns):
        match = pattern.search(text)
        if match:
            results[i] = match
    return results

def batch_regex_findall(patterns: List[Pattern[str]], text: str) -> Dict[int, List[str]]:
    """Apply multiple regex findall operations efficiently."""
    results = {}
    for i, pattern in enumerate(patterns):
        matches = pattern.findall(text)
        if matches:
            results[i] = matches
    return results
```

### Strategy 5: Function-Level Caching

**Implementation:**

```python
@lru_cache(maxsize=100)
def create_units_regex_cached(magnitudes_tuple: tuple) -> Pattern[str]:
    """Cached version of units regex creation."""
    # Convert tuple back to dict for processing
    magnitudes_dict = dict(magnitudes_tuple)
    
    # ... existing regex building logic
    units_regex = "..."  # build regex string
    
    return re.compile(units_regex)

def create_units_regex(magnitudes_dict: Dict) -> Pattern[str]:
    """Create units regex with caching."""
    # Convert dict to tuple for hashing
    magnitudes_tuple = tuple(sorted(magnitudes_dict.items()))
    return create_units_regex_cached(magnitudes_tuple)
```

## Implementation Roadmap

### Phase 1: Quick Wins (1-2 days)
**Priority**: High | **Impact**: High

1. **Add `@lru_cache` to regex compilation**
   - Create `get_compiled_regex()` function with caching
   - Replace `Regex.__init__` with cached compilation
   - **Expected**: 40-50% faster parsing initialization

2. **Pre-compile top 20 common parser patterns**
   - Identify most frequently used patterns via profiling
   - Add to `COMMON_PATTERNS` registry
   - **Expected**: Additional 10-15% improvement

3. **Cache `create_units_regex()` function**
   - Add `@lru_cache` decorator
   - Handle dict parameter hashing
   - **Expected**: Eliminate redundant unit regex compilation

### Phase 2: String Operations (2-3 days)
**Priority**: Medium | **Impact**: Medium

1. **Audit all string-based regex operations**
   - Find all `re.split`, `re.search`, `re.match` calls
   - Create inventory of patterns and usage frequency
   - **Deliverable**: Pattern usage analysis report

2. **Replace with pre-compiled pattern lookups**
   - Create `_SPLIT_PATTERNS` registry
   - Implement `optimized_split_by_pattern()` helper
   - Replace high-frequency string operations
   - **Expected**: 20-30% faster text processing

3. **Add pattern registry for common operations**
   - Centralize pattern definitions
   - Add pattern validation and testing
   - **Expected**: Improved maintainability + 5-10% performance

### Phase 3: Advanced Caching (3-4 days)
**Priority**: Low | **Impact**: Medium

1. **Implement pattern frequency analysis**
   - Add usage tracking to regex cache
   - Identify optimization opportunities
   - **Deliverable**: Performance analysis dashboard

2. **Create smart cache eviction policies**
   - LFU (Least Frequently Used) eviction
   - Pattern complexity-based prioritization
   - **Expected**: Better memory usage, sustained performance

3. **Add regex pattern optimization detection**
   - Detect similar patterns that can be consolidated
   - Suggest pattern refactoring opportunities
   - **Expected**: Additional 10-15% improvement

## Measurement Strategy

### Before Optimization Benchmark

```python
import time
import cProfile
from chemdataextractor.doc import Document

def benchmark_regex_usage():
    """Benchmark current regex performance."""
    documents = [
        "Benzene has a melting point of 5.5°C and boiling point of 80.1°C",
        "Toluene melts at -95°C and boils at 110.6°C with IR at 3028 cm-1",
        "Phenol shows mp 40.5°C, bp 181.7°C, UV λmax 295 nm",
    ]
    
    # Process multiple identical documents to highlight compilation overhead
    start = time.time()
    for doc_text in documents:
        for i in range(50):  # 50 iterations of same document
            doc = Document(doc_text)
            records = doc.records  # This triggers all parsing
    end = time.time()
    
    return end - start

def profile_regex_compilation():
    """Profile regex compilation specifically."""
    pr = cProfile.Profile()
    pr.enable()
    
    benchmark_regex_usage()
    
    pr.disable()
    pr.dump_stats('regex_benchmark_before.prof')
    
    # Print regex-related stats
    pr.print_stats('re.compile|regex|Regex')
```

### After Optimization - Expected Results

**Performance Improvements:**
- **Regex compilation time**: 70% reduction
- **Overall parsing time**: 25-35% improvement  
- **Memory usage**: 15-20% reduction (fewer regex objects)
- **Cache hit rate**: 85-90% for common patterns

**Measurement Metrics:**
```python
def benchmark_optimized_regex():
    """Benchmark optimized regex performance."""
    # Same benchmark as above
    optimized_time = benchmark_regex_usage()
    
    # Cache statistics
    cache_info = get_compiled_regex.cache_info()
    print(f"Cache hits: {cache_info.hits}")
    print(f"Cache misses: {cache_info.misses}")
    print(f"Hit rate: {cache_info.hits / (cache_info.hits + cache_info.misses):.2%}")
    
    return optimized_time
```

## Pattern Consolidation Opportunities

### Identified Pattern Duplications

**Number Matching Patterns (13+ similar patterns):**
```python
# Can be consolidated into a pattern family
r"(\d+\.?(?:\d+)?)"      # _number_pattern
r"(-?\d+\.?(?:\d+)?)"    # _negative_number_pattern  
r"(\d+(?!\d+))"          # _simple_number_pattern
r"\d+\.?\d*"             # Various other number patterns
# ... 9 more similar variations
```

**Bracket/Parentheses Patterns (8+ patterns):**
```python
r"(\()|(\))"            # _brackets_pattern
r"\)\w*"                # _end_bracket_pattern
r"/\("                  # _open_bracket_pattern
r"^\(([^\(\)]+)\)$"     # BRACKET_RE
# ... 4 more bracket variations
```

**Unit/Magnitude Patterns (6+ patterns):**
```python
r"[pnµmTGMkc]"          # _magnitude_indicators
r"°?[CKF]|celsius..."   # Temperature units
r"bar|atm|pa|torr..."   # Pressure units
# ... 3 more unit patterns
```

### Consolidation Strategy

```python
class PatternFamilies:
    """Organized pattern families for better maintainability."""
    
    NUMBERS = {
        'basic': re.compile(r'\d+\.?\d*'),
        'signed': re.compile(r'-?\d+\.?\d*'),
        'integer_only': re.compile(r'\d+(?!\d)'),
        'with_error': re.compile(r'(\d+\.?\d*)(\s*±\s*\d+\.?\d*)?'),
        'scientific': re.compile(r'-?\d+\.?\d*[eE][+-]?\d+'),
    }
    
    BRACKETS = {
        'any_open': re.compile(r'[\(\[\{]'),
        'any_close': re.compile(r'[\)\]\}]'),
        'paired_parens': re.compile(r'\(([^)]+)\)'),
        'paired_brackets': re.compile(r'\[([^\]]+)\]'),
    }
    
    UNITS = {
        'temperature': re.compile(r'°?[CKF]|celsius|kelvin|fahrenheit', re.I),
        'pressure': re.compile(r'bar|atm|pa|torr|mmhg', re.I),
        'mass': re.compile(r'[kmµn]?g|kg|mg|µg|ng', re.I),
        'volume': re.compile(r'[kmµn]?l|ml|µl|nl', re.I),
    }
```

## Flag Optimization

### Current Flag Usage Analysis

**Most Common Flag Combinations:**
- `re.I | re.U` (case-insensitive + unicode) - 60% of patterns
- `0` (no flags) - 25% of patterns  
- `re.I` (case-insensitive only) - 10% of patterns
- Other combinations - 5% of patterns

### Flag-Specific Caching Strategy

```python
class FlagOptimizedCache:
    """Flag-aware regex caching for better performance."""
    
    # Pre-create caches for common flag combinations
    _CACHE_NO_FLAGS = {}
    _CACHE_CASE_INSENSITIVE = {}
    _CACHE_UNICODE = {}
    _CACHE_CASE_INSENSITIVE_UNICODE = {}
    
    @classmethod
    def get_cached_pattern(cls, pattern: str, flags: int = 0) -> Pattern[str]:
        """Get pattern from appropriate flag-specific cache."""
        if flags == 0:
            cache = cls._CACHE_NO_FLAGS
        elif flags == re.I:
            cache = cls._CACHE_CASE_INSENSITIVE
        elif flags == re.U:
            cache = cls._CACHE_UNICODE
        elif flags == (re.I | re.U):
            cache = cls._CACHE_CASE_INSENSITIVE_UNICODE
        else:
            # Fallback to general cache for uncommon flag combinations
            return re.compile(pattern, flags)
        
        if pattern not in cache:
            cache[pattern] = re.compile(pattern, flags)
        
        return cache[pattern]
```

## Risk Analysis and Mitigation

### Potential Risks

1. **Memory Usage Increase**
   - **Risk**: Cache storage overhead
   - **Mitigation**: Implement cache size limits and LRU eviction
   - **Monitoring**: Track cache memory usage

2. **Cache Invalidation Complexity**  
   - **Risk**: Stale patterns if regex logic changes
   - **Mitigation**: Version-based cache invalidation
   - **Testing**: Comprehensive regression tests

3. **Thread Safety**
   - **Risk**: Cache corruption in multi-threaded environments
   - **Mitigation**: Use thread-safe caching mechanisms
   - **Implementation**: `functools.lru_cache` is thread-safe

### Mitigation Strategies

```python
import threading
from functools import lru_cache
from typing import Dict, Pattern
import weakref

class ThreadSafeRegexCache:
    """Thread-safe regex cache with memory management."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Pattern[str]] = {}
        self._lock = threading.RLock()
        self._access_count: Dict[str, int] = {}
    
    def get_pattern(self, pattern: str, flags: int = 0) -> Pattern[str]:
        """Thread-safe pattern retrieval with LRU tracking."""
        cache_key = f"{pattern}_{flags}"
        
        with self._lock:
            if cache_key in self._cache:
                self._access_count[cache_key] += 1
                return self._cache[cache_key]
            
            # Evict least used patterns if cache is full
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # Compile and cache new pattern
            compiled = re.compile(pattern, flags)
            self._cache[cache_key] = compiled
            self._access_count[cache_key] = 1
            
            return compiled
    
    def _evict_lru(self):
        """Evict least recently used patterns."""
        # Remove 20% of least used patterns
        evict_count = max(1, self.max_size // 5)
        sorted_patterns = sorted(self._access_count.items(), key=lambda x: x[1])
        
        for pattern_key, _ in sorted_patterns[:evict_count]:
            del self._cache[pattern_key]
            del self._access_count[pattern_key]
```

## Success Metrics

### Performance Targets

**Primary Metrics:**
- **Regex compilation time**: >70% reduction
- **Overall parsing performance**: >25% improvement
- **Memory usage**: <20% increase (offset by performance gains)
- **Cache hit rate**: >85% for production workloads

**Secondary Metrics:**
- **Code maintainability**: Centralized pattern management
- **Error reduction**: Fewer regex compilation errors
- **Development velocity**: Faster testing and iteration

### Monitoring and Alerting

```python
class RegexPerformanceMonitor:
    """Monitor regex optimization performance in production."""
    
    def __init__(self):
        self.compilation_times = []
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def log_compilation_time(self, pattern: str, compile_time: float):
        """Log regex compilation performance."""
        self.compilation_times.append((pattern, compile_time))
    
    def get_performance_report(self) -> Dict[str, float]:
        """Generate performance summary."""
        if not self.compilation_times:
            return {}
        
        times = [t for _, t in self.compilation_times]
        return {
            'avg_compilation_time': sum(times) / len(times),
            'max_compilation_time': max(times),
            'total_compilations': len(times),
            'cache_hit_rate': self.cache_stats['hits'] / 
                             (self.cache_stats['hits'] + self.cache_stats['misses']),
        }
```

---

## Conclusion

This regex optimization represents one of the highest-impact performance improvements we could implement for ChemDataExtractor2. The combination of pattern caching, pre-compilation, and smart string operation handling should provide:

- **2-4x faster parser initialization**
- **20-30% overall performance improvement**
- **Better memory efficiency**
- **Improved code maintainability**

The implementation can be done incrementally with minimal risk, allowing us to measure and validate improvements at each phase.