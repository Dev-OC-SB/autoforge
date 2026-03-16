#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
"""
Streaming Test
==============

Test streaming functionality with OpenRouter.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()


async def test_streaming():
    """Test streaming with OpenRouter."""
    print("=" * 70)
    print("STREAMING TEST")
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
        test_project = Path("/tmp/test_seaforge_streaming")
        test_project.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "=" * 70)
        print("TEST 1: Non-Streaming Mode (Default)")
        print("=" * 70)
        
        client = await create_unified_client(
            project_dir=test_project,
            model="anthropic/claude-3.5-sonnet",
            yolo_mode=True,
            agent_type="coding",
            provider_override="openrouter"
        )
        
        async with client:
            await client.query("Write a haiku about coding. Just the haiku, nothing else.")
            
            print("Response (non-streaming):")
            async for msg in client.receive_response():
                if hasattr(msg, "content"):
                    for block in msg.content:
                        if hasattr(block, "text"):
                            print(block.text)
        
        print("\n" + "=" * 70)
        print("TEST 2: Streaming Mode")
        print("=" * 70)
        
        client = await create_unified_client(
            project_dir=test_project,
            model="anthropic/claude-3.5-sonnet",
            yolo_mode=True,
            agent_type="coding",
            provider_override="openrouter"
        )
        
        async with client:
            await client.query("Write a haiku about AI. Just the haiku, nothing else.", stream=True)
            
            print("Response (streaming - tokens appear as they arrive):")
            async for msg in client.receive_response():
                if hasattr(msg, "content"):
                    for block in msg.content:
                        if hasattr(block, "text"):
                            # In streaming mode, we get incremental updates
                            # Print with carriage return to show progress
                            print(f"\r{block.text}", end='', flush=True)
            print()  # Final newline
        
        print("\n" + "=" * 70)
        print("✅ STREAMING TESTS PASSED")
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
    success = asyncio.run(test_streaming())
    exit(0 if success else 1)
