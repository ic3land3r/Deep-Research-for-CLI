import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.orchestrator import Orchestrator

async def main():
    print("--- Starting Cycle 1 Validation ---")
    topic = "The impact of quantum computing on cryptography"
    
    try:
        orchestrator = Orchestrator()
        result = await orchestrator.run(topic)
        
        print("\n--- Final Report ---")
        print(result)
        print("\n--- Validation Successful ---")
    except Exception as e:
        print(f"\n--- Validation Failed: {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
