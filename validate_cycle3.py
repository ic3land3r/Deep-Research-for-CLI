import asyncio
import os
import sys
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.orchestrator import Orchestrator

async def main():
    print("--- Starting Cycle 3 Validation (Parallel + Feedback) ---")
    topic = "Compare the technical specifications of the iPhone 16 Pro and the Google Pixel 9 Pro."
    
    try:
        orchestrator = Orchestrator()
        
        start_time = time.time()
        result = await orchestrator.run(topic)
        end_time = time.time()
        
        print("\n--- Final Report ---")
        print(result)
        print(f"\n--- Validation Successful in {end_time - start_time:.2f} seconds ---")
    except Exception as e:
        print(f"\n--- Validation Failed: {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
