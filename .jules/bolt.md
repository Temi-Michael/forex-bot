## 2026-06-02 - Python String Formatting vs Math for Digit Extraction
**Learning:** Python string formatting (`f"{val:.Xf}"`) is relatively slow when used in high-frequency loops (like processing every incoming tick in a trading bot). Profiling showed string allocation/formatting takes roughly 2x longer than pure mathematical extraction (`int(round(price * 10**pip_size)) % 10`).
**Action:** When extracting specific digits from floats in tight loops in Python, prefer mathematical operations over string coercion to avoid unnecessary memory allocations and parsing overhead.
