# ChemDataExtractor2 Document Processing Hierarchy

## Document Scope Hierarchy

```
📄 Document (DocumentRange)
├── 📑 Section (SectionRange)
│   ├── 📋 Heading
│   │   ├── 📖 Sentence
│   │   └── 🔍 Records
│   ├── 📝 Paragraph (ParagraphRange)
│   │   ├── 📖 Sentence (SentenceRange)
│   │   │   ├── 🏷️  Token (word-level)
│   │   │   └── 🔍 Records (extracted at sentence level)
│   │   └── 📖 Sentence (SentenceRange)
│   ├── 📊 Table
│   │   ├── 📋 Row
│   │   │   ├── 📦 Cell
│   │   │   │   ├── 📖 Sentence (SentenceRange)
│   │   │   │   └── 🔍 Records
│   │   │   └── 📦 Cell
│   │   └── 📋 Row
│   └── 🖼️  Figure
│       ├── 📝 Caption
│       │   ├── 📖 Sentence (SentenceRange)
│       │   └── 🔍 Records
│       └── 🖼️  Image Data
└── 📝 Footnote
    ├── 📖 Sentence (SentenceRange)
    └── 🔍 Records
```

## Processing Flow by Scope

### 1. Sentence-Level Processing (Primary)
```
📖 Sentence: "The melting point was 100°C using H2O."
    ↓ [Parsers run on sentence]
    🔍 Records extracted:
    ├── MeltingPoint(value=100, units='°C')
    └── Apparatus(name='H2O') ❌ [BUG - now fixed!]
```

### 2. Document-Level Contextual Merging
```
📄 Document scope:
    📖 Sentence 1: "The melting point was 100°C." → MeltingPoint
    📖 Sentence 2: "H2O was used as solvent."     → Compound(H2O)

    ↓ [Contextual merging across sentences]

    🔗 Merged: MeltingPoint(value=100, compound=H2O)
```

## Contextual Range Scopes

### Distance-Based Merging
```
📄 Document
├── 📑 Section 1
│   ├── 📝 Paragraph A
│   │   ├── 📖 Sentence 1 ←────┐
│   │   ├── 📖 Sentence 2      │ SentenceRange (closest)
│   │   └── 📖 Sentence 3 ←────┘
│   └── 📝 Paragraph B ←──────── ParagraphRange (medium)
├── 📑 Section 2 ←─────────────── SectionRange (far)
└── 📑 Section 3 ←─────────────── DocumentRange (furthest)
```

### Merging Priority (closest wins)
1. **Same Sentence** (distance = 0)
2. **Adjacent Sentences** (distance = 1 SentenceRange)
3. **Same Paragraph** (distance = 1 ParagraphRange)
4. **Same Section** (distance = 1 SectionRange)
5. **Different Sections** (distance = 1+ DocumentRange)

## Model Application Scope

### Where Models Run
```
📄 Document
├── 📝 Paragraph
│   └── 📖 Sentence ← 🎯 PRIMARY: Models run here
├── 📊 Table
│   └── 📦 Cell
│       └── 📖 Sentence ← 🎯 Models run here too
├── 🖼️  Figure
│   └── 📝 Caption
│       └── 📖 Sentence ← 🎯 Models run here too
└── 📑 Heading ← 🎯 Models run here (as sentence)
```

### Model Types by Scope
```
📖 Sentence Level:
├── 🧪 Compound Parser
├── 🌡️  MeltingPoint Parser
├── 🔬 Apparatus Parser
├── 📊 NMR Parser
└── 📈 IR Parser

📄 Document Level:
├── 🔗 Contextual Merging
├── 📋 Record Deduplication
└── 🎯 Cross-reference Resolution
```

## Example: Real Processing Flow

### Input Text
```
"The synthesized compound was characterized by melting point determination.
The melting point was found to be 89-91°C.
H2O was used as solvent for recrystallization."
```

### Processing Breakdown
```
📄 Document
└── 📝 Paragraph
    ├── 📖 Sentence 1: "The synthesized compound was characterized..."
    │   └── 🔍 Records: [Compound] (generic)
    ├── 📖 Sentence 2: "The melting point was found to be 89-91°C."
    │   └── 🔍 Records: [MeltingPoint(89-91°C)]
    └── 📖 Sentence 3: "H2O was used as solvent..."
        └── 🔍 Records: [Compound(H2O)]

↓ Document-Level Contextual Merging

📄 Final Records:
├── 🔗 MeltingPoint(89-91°C, compound=H2O)
└── 🧪 Compound(H2O)
```

## Key Insights

1. **Sentence = Atomic Processing Unit**: All initial parsing happens at sentence level
2. **Document = Merging Scope**: Contextual relationships resolved across sentences
3. **Hierarchical Structure**: Each level has specific responsibilities
4. **Distance Matters**: Closer records have higher merge priority
5. **Bug Location**: The H2O apparatus bug occurred at sentence-level parsing, not document-level merging
