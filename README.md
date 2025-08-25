# Ultimate Data Extractor v4 (Modular)

Modular reorganization of the monolithic extractor into a clean package:

- core: search engine and aggregator
- models: enums and dataclasses
- sources: registry, factory, fetcher
- ai: extractors (Groq) and validators
- infrastructure: cache, rate limits, metrics
- cli: minimal demo

Usage (Python):

```python
from ultimate_data_extractor_v4.main import extract_ultimate_pure_data
```

CLI demo:

```bash
python -m ultimate_data_extractor_v4.cli.main
```

Requires env var `GROQ_API_KEY`.