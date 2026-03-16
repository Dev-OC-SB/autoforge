# OpenRouter Setup Instructions

## Phase 1 Testing - Quick Start

To test the multi-provider integration with OpenRouter, you need to set your API key.

### Option 1: Environment Variable (Recommended for Testing)

```bash
export OPENROUTER_API_KEY=your-api-key-here
```

Then run the tests:
```bash
cd /root/seaforge
./venv/bin/python test_unified_client.py
```

### Option 2: Create .env File

Create a `.env` file in `/root/seaforge/`:
```bash
cd /root/seaforge
echo "OPENROUTER_API_KEY=your-api-key-here" > .env
```

Then run the tests:
```bash
./venv/bin/python test_unified_client.py
```

### Option 3: Manual Test Script

Run the manual test script:
```bash
export OPENROUTER_API_KEY=your-api-key-here
./venv/bin/python test_openrouter_manual.py
```

## Expected Results

When properly configured, you should see:
- ✓ Provider detection finds OpenRouter
- ✓ Adapter client creates successfully
- ✓ Unified client creates successfully
- ✓ Message adapters work correctly
- ✓ Simple query executes and returns response

## Next Steps

Once Phase 1 tests pass, we'll proceed to Phase 2 (streaming implementation).
