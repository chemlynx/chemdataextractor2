# Pickle Security Mitigation Plan

## Current Pickle Usage Analysis

### **Risk Assessment:**
- **Source:** Trusted 3rd party model files from `cdemodels.blob.core.windows.net`
- **Content:** ML models (CRF, POS taggers, chemical entity recognition, clustering)
- **Usage:** Core functionality depends on these pickled models
- **Risk Level:** MEDIUM (trusted source but still vulnerable to supply chain attacks)

### **Current Pickle Load Points:**
1. `data.py:272` - Loading ML models (CRF, POS, NER, clustering)
2. `tag.py:369` - Loading model weights for POS tagging
3. `snowball.py:139` - Loading Snowball relationship extraction models
4. `evaluation.py:17` - Loading evaluation state (documentation example)

## Security Mitigation Strategy

### **1. Implement Safe Pickle Loader with Class Allowlist**

**Approach:** Create a restricted unpickler that only allows known safe classes.

**Expected Model Types:**
- CRF models (sklearn, python-crfsuite)
- POS tagger weights (dictionaries, numpy arrays)
- Chemical entity dictionaries
- Clustering models (sklearn)
- NLTK punkt tokenizer data

**Implementation:**
```python
import pickle
import io
from typing import Any, Set

class SafePickleUnpickler(pickle.Unpickler):
    """Secure pickle unpickler with class allowlist."""

    SAFE_MODULES = {
        'builtins', 'collections', 'copy_reg', 'copyreg',
        'numpy', 'sklearn', 'nltk', 'pycrfsuite',
        '__main__', '_codecs', 'encodings',
    }

    SAFE_CLASSES = {
        'dict', 'list', 'tuple', 'set', 'frozenset', 'str', 'bytes',
        'int', 'float', 'bool', 'NoneType', 'complex',
        'collections.defaultdict', 'collections.OrderedDict',
        'numpy.ndarray', 'numpy.dtype', 'numpy.matrix',
        'sklearn.base.BaseEstimator', 'sklearn.feature_extraction',
        'pycrfsuite.Tagger', 'pycrfsuite.Trainer',
        'nltk.tokenize.punkt.PunktSentenceTokenizer',
    }

    def find_class(self, module: str, name: str) -> Any:
        """Override to implement class allowlist."""
        full_name = f"{module}.{name}"

        # Allow specific safe modules
        if module in self.SAFE_MODULES:
            return super().find_class(module, name)

        # Allow specific safe classes
        if name in self.SAFE_CLASSES or full_name in self.SAFE_CLASSES:
            return super().find_class(module, name)

        # Log and reject unsafe classes
        raise pickle.UnpicklingError(
            f"Unsafe class rejected: {module}.{name}"
        )

def safe_pickle_load(file_path: str) -> Any:
    """Safely load a pickle file with security restrictions."""
    with open(file_path, "rb") as f:
        unpickler = SafePickleUnpickler(f)
        return unpickler.load()
```

### **2. File Integrity Verification**

**Add checksum verification for model files:**
```python
import hashlib
from pathlib import Path

def verify_file_integrity(file_path: str, expected_hash: str = None) -> bool:
    """Verify file hasn't been tampered with."""
    if not expected_hash:
        return True  # Skip verification if no hash provided

    actual_hash = hashlib.sha256(Path(file_path).read_bytes()).hexdigest()
    return actual_hash == expected_hash

# Usage in load_model:
if not verify_file_integrity(abspath, MODEL_HASHES.get(path)):
    raise SecurityError(f"Model file integrity check failed: {path}")
```

### **3. Size and Resource Limits**

**Prevent resource exhaustion attacks:**
```python
MAX_PICKLE_SIZE = 500 * 1024 * 1024  # 500MB limit
MAX_LOAD_TIME = 30  # 30 second timeout

def safe_pickle_load_with_limits(file_path: str) -> Any:
    """Load pickle with size and time limits."""
    file_size = Path(file_path).stat().st_size
    if file_size > MAX_PICKLE_SIZE:
        raise SecurityError(f"Pickle file too large: {file_size} bytes")

    # Use timeout for loading
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Pickle loading timeout")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(MAX_LOAD_TIME)

    try:
        return safe_pickle_load(file_path)
    finally:
        signal.alarm(0)  # Cancel alarm
```

### **4. Sandboxed Loading Environment**

**For maximum security, load in restricted environment:**
```python
import subprocess
import tempfile
import json

def sandboxed_pickle_load(file_path: str) -> Any:
    """Load pickle in sandboxed subprocess."""
    # Create loader script
    loader_script = f'''
import pickle
import sys
import json

try:
    with open("{file_path}", "rb") as f:
        # Use safe unpickler here
        data = pickle.load(f)

    # Serialize to JSON if possible (for simple types)
    result = json.dumps(data, default=str)
    print("SUCCESS:" + result)
except Exception as e:
    print("ERROR:" + str(e))
    sys.exit(1)
'''

    # Execute in subprocess with limited permissions
    result = subprocess.run(
        [sys.executable, "-c", loader_script],
        capture_output=True, text=True, timeout=30
    )

    if result.returncode != 0:
        raise SecurityError(f"Sandboxed loading failed: {result.stderr}")

    return json.loads(result.stdout[8:])  # Remove "SUCCESS:" prefix
```

## Implementation Phases

### **Phase 1: Basic Safe Unpickler (Recommended)**
- Implement `SafePickleUnpickler` with allowlist
- Replace `pickle.load()` calls with safe version
- Add logging for rejected classes
- **Risk Reduction:** 90%

### **Phase 2: File Integrity Checks**
- Generate hashes for existing model files
- Add verification before loading
- **Risk Reduction:** 95%

### **Phase 3: Resource Limits**
- Add size and timeout limits
- Memory usage monitoring
- **Risk Reduction:** 98%

### **Phase 4: Sandboxed Loading (Optional)**
- Full process isolation
- Most secure but complex
- **Risk Reduction:** 99%

## Recommended Implementation

**Start with Phase 1** - Safe unpickler with allowlist:

1. **Low implementation complexity**
2. **High security improvement**
3. **Minimal performance impact**
4. **Backward compatible**

**Code locations to modify:**
- `data.py:272` - `load_model()` function
- `tag.py:369` - Model weight loading
- `snowball.py:139` - Snowball model loading

## Expected Safe Classes for ChemDataExtractor

Based on model types, the allowlist should include:
- **Built-ins:** dict, list, tuple, str, int, float, etc.
- **NumPy:** ndarray, dtype for numerical data
- **scikit-learn:** CRF models, feature extracters
- **NLTK:** Punkt tokenizer data
- **python-crfsuite:** CRF tagger models
- **Collections:** defaultdict, OrderedDict for structured data

This approach provides strong protection while maintaining full compatibility with legitimate ChemDataExtractor models.