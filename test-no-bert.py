#!/usr/bin/env python3
"""
Ultra-fast test runner that mocks BERT models for rapid testing of logic,
without the 15+ second BERT initialization overhead.
"""
import os
import sys
import subprocess
import tempfile

# Mock BERT initialization to speed up tests
MOCK_BERT_CODE = '''
import os
import sys

# Mock the BERT components before they get imported
class MockBertCrfTagger:
    def __init__(self, *args, **kwargs):
        pass

    def tag(self, sentence):
        # Return minimal mock data for basic testing
        return ['O'] * len(sentence.tokens)

    def batch_tag(self, sentences):
        return [self.tag(s) for s in sentences]

class MockBertCrfModel:
    def __init__(self, *args, **kwargs):
        pass

# Mock the expensive imports
sys.modules['chemdataextractor.nlp.bertcrf_tagger'] = type(sys)('mock_bert')
sys.modules['chemdataextractor.nlp.bertcrf_tagger'].BertCrfTagger = MockBertCrfTagger
sys.modules['chemdataextractor.nlp.bertcrf_tagger'].BertCrfModel = MockBertCrfModel

# Set environment to skip model loading
os.environ['CDE_TESTING_MODE'] = '1'
os.environ['CDE_SKIP_BERT_INIT'] = '1'
'''

def create_mock_test_file(test_pattern):
    """Create a temporary test file that mocks BERT for speed."""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(MOCK_BERT_CODE)
        f.write('\\n')
        f.write('# Now run the actual test\\n')
        f.write(f'import subprocess\\n')
        f.write(f'import sys\\n')
        f.write(f'import os\\n')
        f.write(f'\\n')
        f.write(f'# Run pytest with mocked environment\\n')
        f.write(f'env = os.environ.copy()\\n')
        f.write(f'env["PYTHONPATH"] = os.pathsep.join([os.getcwd()] + sys.path)\\n')
        f.write(f'\\n')
        f.write(f'cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short", "--no-cov", "{test_pattern}"]\\n')
        f.write(f'result = subprocess.run(cmd, env=env)\\n')
        f.write(f'sys.exit(result.returncode)\\n')

        return f.name

def main():
    if len(sys.argv) < 2:
        print("Usage: python test-no-bert.py <test_pattern>")
        print("Example: python test-no-bert.py tests/test_extract.py::TestExtract::test_melting_point_heading_salt")
        sys.exit(1)

    test_pattern = sys.argv[1]

    # Create mock test file
    mock_file = create_mock_test_file(test_pattern)

    try:
        print(f"Running test with mocked BERT: {test_pattern}")

        # Run the mock test file
        result = subprocess.run([sys.executable, mock_file])
        return result.returncode

    finally:
        # Clean up
        try:
            os.unlink(mock_file)
        except:
            pass

if __name__ == '__main__':
    sys.exit(main())