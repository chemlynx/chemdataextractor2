#!/usr/bin/env python
"""
Debug Trigger Phrase Extraction

Investigate why the optimized system isn't matching triggers properly.
"""

from chemdataextractor.doc import Document
from chemdataextractor.parse.mp_new import MpParser
from chemdataextractor.parse.optimized_triggers import TriggerPhraseIndex


def debug_trigger_extraction():
    print("🔍 Debugging Trigger Phrase Extraction")
    print("=" * 50)

    # Create parser and test document
    parser = MpParser()
    doc = Document("The melting point of the compound is 125°C under standard conditions.")
    sentence = doc.sentences[0]

    print(f"Test sentence: '{sentence.text}'")
    print(f"Sentence tokens: {[token.text for token in sentence.tokens]}")

    # Check original trigger phrase
    print(f"\nOriginal trigger phrase: {parser.trigger_phrase}")
    print(f"Trigger phrase type: {type(parser.trigger_phrase)}")

    # Deep inspection of trigger phrase structure
    if parser.trigger_phrase:
        print(f"Has exprs: {hasattr(parser.trigger_phrase, 'exprs')}")
        if hasattr(parser.trigger_phrase, "exprs"):
            print(f"Number of expressions: {len(parser.trigger_phrase.exprs)}")
            for i, expr in enumerate(parser.trigger_phrase.exprs):
                print(f"  Expression {i + 1}: {expr} (type: {type(expr)})")
                if hasattr(expr, "name"):
                    print(f"    - name: {expr.name}")
                if hasattr(expr, "pattern"):
                    print(f"    - pattern: {expr.pattern}")
                if hasattr(expr, "match"):
                    print(f"    - match: {expr.match}")
                if hasattr(expr, "exprs"):
                    print(f"    - has sub-expressions: {len(expr.exprs)}")
                    # Dive one level deeper
                    for j, subexpr in enumerate(expr.exprs[:3]):  # Show first 3
                        print(f"      Sub-expr {j + 1}: {subexpr} (type: {type(subexpr)})")
                        if hasattr(subexpr, "match"):
                            print(f"        - match: {subexpr.match}")
                        if hasattr(subexpr, "pattern"):
                            print(f"        - pattern: {subexpr.pattern}")
                if hasattr(expr, "expr"):
                    print(f"    - has inner expr: {expr.expr} (type: {type(expr.expr)})")
                    if hasattr(expr.expr, "match"):
                        print(f"      - inner match: {expr.expr.match}")
                    if hasattr(expr.expr, "exprs"):
                        print(f"      - inner sub-expressions: {len(expr.expr.exprs)}")
                        for k, innerexpr in enumerate(expr.expr.exprs[:3]):
                            print(
                                f"        Inner-expr {k + 1}: {innerexpr} (type: {type(innerexpr)})"
                            )
                            if hasattr(innerexpr, "match"):
                                print(f"          - match: {innerexpr.match}")

        # Test original trigger matching
        original_results = list(parser.trigger_phrase.scan(sentence.tokens))
        print(f"Original scan results: {len(original_results)} matches")
        for i, result in enumerate(original_results[:3]):  # Show first 3
            print(f"  Match {i + 1}: {result}")

    # Test trigger phrase extraction
    print("\n📊 Testing TriggerPhraseIndex extraction...")
    index = TriggerPhraseIndex()

    if hasattr(parser, "trigger_phrase") and parser.trigger_phrase:
        phrases = index._extract_trigger_phrases(parser.trigger_phrase)
        print(f"Extracted phrases: {phrases}")

        # Add parser to index
        index.add_parser(parser)
        index.compile()

        # Test text matching
        text = " ".join([token.text for token in sentence.tokens])
        print(f"Text for matching: '{text}'")

        candidates = index.get_candidate_parsers(text)
        print(f"Candidate parsers: {len(candidates)}")

        # Debug index contents
        print(f"\nIndex statistics: {index.get_stats()}")
        print(f"Simple phrases: {index.simple_phrases}")
        print(f"Compiled patterns: {list(index.compiled_patterns.keys())}")

        # Test bloom filter
        for phrase in phrases[:3]:  # Check first few phrases
            contains = index.bloom_filter.might_contain(phrase.lower())
            print(f"Bloom filter contains '{phrase}': {contains}")


if __name__ == "__main__":
    debug_trigger_extraction()
