#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
"""
Manual OpenRouter Test
=======================

Simple test to verify OpenRouter integration works end-to-end.
"""

import asyncio
import os
from pathlib import Path


async def test_openrouter():
    """Test OpenRouter integration manually."""
    print("=" * 70)
    print("OPENROUTER INTEGRATION TEST")
    print("=" * 70)
    
    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set!")
        print("   Please set it: export OPENROUTER_API_KEY=your-key-here")
        return False
    
    print(f"✓ API key found: {api_key[:20]}...")
    
    try:
        from core.client import create_unified_client
        
        # Create test project directory
        test_project = Path("/tmp/test_seaforge_openrouter")
        test_project.mkdir(parents=True, exist_ok=True)
        
        print("\n1. Creating unified client...")
        client = await create_unified_client(
            project_dir=test_project,
            model="anthropic/claude-3.5-sonnet",
            yolo_mode=True,
            agent_type="coding",
            provider_override="openrouter"
        )
        
        print(f"   ✓ Client created")
        print(f"   Provider: {client.get_provider_type()}")
        print(f"   Model: {client.get_model()}")
        
        print("\n2. Sending test query...")
        async with client:
            await client.query("Say 'Hello from SeaForge!' and nothing else.")
            
            print("   Receiving response...")
            response_text = ""
            async for msg in client.receive_response():
                if hasattr(msg, "content"):
                    for block in msg.content:
                        if hasattr(block, "text"):
                            response_text += block.text
                            print(f"   Response: {block.text}")
        
        print("\n3. Checking usage stats...")
        stats = client.get_usage_stats()
        if stats:
            print(f"   ✓ Input tokens: {stats['input_tokens']}")
            print(f"   ✓ Output tokens: {stats['output_tokens']}")
            print(f"   ✓ Cost: ${stats['cost_usd']:.6f}")
        else:
            print("   ⚠ No usage stats available")
        
        print("\n" + "=" * 70)
        print("✅ TEST PASSED - OpenRouter integration working!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_openrouter())
    exit(0 if success else 1)
