---
name: test-dsp
description: Test the DSP pipeline with audio analysis
disable-model-invocation: true
---

Test the Stetho DSP pipeline by running it on test data and reporting results.

## Steps

1. Run a Python script that:
   - Creates a synthetic test signal (mix of heart-like frequencies + noise)
   - Processes it through the DSP pipeline in each mode (cardiac, respiratory, raw)
   - Measures SNR before and after processing
   - Reports frequency content analysis

2. Use this test code pattern:
```python
import numpy as np
from backend.config import SAMPLE_RATE, CHUNK_SIZE
from backend.dsp.pipeline import DSPPipeline

# Generate test signal: 40Hz (S1) + 80Hz (S2) + white noise
t = np.linspace(0, CHUNK_SIZE / SAMPLE_RATE, CHUNK_SIZE, dtype=np.float32)
heart = 0.5 * np.sin(2 * np.pi * 40 * t) + 0.3 * np.sin(2 * np.pi * 80 * t)
noise = 0.4 * np.random.randn(CHUNK_SIZE).astype(np.float32)
signal = heart + noise

for mode in ["cardiac", "respiratory", "raw"]:
    pipeline = DSPPipeline(mode=mode)
    # Process multiple chunks to let filters settle
    for _ in range(10):
        result = pipeline.process(signal.copy())
    # Analyze result
```

3. Report:
   - SNR improvement per mode
   - Whether cardiac mode correctly emphasizes 20-60 Hz
   - Whether respiratory mode correctly emphasizes 300-600 Hz
   - Any clipping or artifacts detected

Run from the project root: `cd C:/Users/Medhi Souai/Desktop/stetho`
