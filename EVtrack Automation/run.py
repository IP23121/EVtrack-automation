#!/usr/bin/env python3
"""Simple EVTrack API starter"""

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting EVTrack API on localhost:3000...")
    print("🔑 API Key: evtrack")
    uvicorn.run("api.main:app", host="0.0.0.0", port=3000, reload=True)
