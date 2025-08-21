#!/usr/bin/env python3
"""Simple EVTrack API starter - First-time user friendly"""

import sys
import subprocess
import os
import shutil

def install_if_missing():
    """Install packages if missing"""
    packages = ['uvicorn', 'fastapi', 'selenium', 'python-multipart', 'python-dotenv', 'requests', 'Pillow', 'webdriver-manager']
    missing_packages = []
    
    for pkg in packages:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing_packages.append(pkg)
    
    if missing_packages:
        print(f" Installing {len(missing_packages)} required packages...")
        for pkg in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--user", "--quiet"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--break-system-packages", "--quiet"],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except:
                    print(f" Failed to install {pkg}. Please install manually: pip install {pkg}")
                    return False
    return True

def setup_env_file():
    """Setup .env file if it doesn't exist"""
    env_file = ".env"
    env_example = ".env.example"
    
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            shutil.copy(env_example, env_file)
            print(" Created .env file from template")
            print(" IMPORTANT: Edit .env file with your EVTrack credentials before first use!")
            print("   - Set EVTRACK_EMAIL to your email")
            print("   - Set EVTRACK_PASSWORD to your password")
            return False
        else:
            # Create basic .env file
            with open(env_file, 'w') as f:
                f.write("""# EVTrack Automation Environment Variables
EVTRACK_EMAIL=your-email@example.com
EVTRACK_PASSWORD=your-password
API_KEYS=evtrack
HEADLESS_MODE=False
""")
            print(" Created basic .env file")
            print(" IMPORTANT: Edit .env file with your EVTrack credentials!")
            return False
    return True

def check_credentials():
    """Check if credentials are configured"""
    from dotenv import load_dotenv
    load_dotenv()
    
    email = os.getenv("EVTRACK_EMAIL")
    password = os.getenv("EVTRACK_PASSWORD")
    
    if not email or email == "your-email@example.com":
        print(" Please set your EVTRACK_EMAIL in the .env file")
        return False
    
    if not password or password == "your-password":
        print(" Please set your EVTRACK_PASSWORD in the .env file")
        return False
    
    return True

if __name__ == "__main__":
    print(" EVTrack Automation Setup")
    print("=" * 40)
    
    # Install packages
    if not install_if_missing():
        print(" Package installation failed. Please check your Python environment.")
        sys.exit(1)
    
    # Setup environment
    if not setup_env_file():
        print("\n⏸  Setup paused. Please configure .env file and run again.")
        sys.exit(0)
    
    # Check credentials
    if not check_credentials():
        print("\n⏸  Please configure your EVTrack credentials in .env file and run again.")
        sys.exit(0)
    
    # Start server
    try:
        import uvicorn
        print("\n All checks passed!")
        print(" Starting EVTrack API on http://localhost:3000/docs")
        print(" API Key: evtrack")
        print(" Documentation: http://localhost:3000/docs")
        print("\n Tip: Keep this window open while using the API")
        print(" Press Ctrl+C to stop the server")
        print("-" * 50)
        
        uvicorn.run("api.main:app", host="0.0.0.0", port=3000, reload=True)
    except ImportError:
        print(" uvicorn not available. Please install manually: pip install uvicorn")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n Server stopped. Goodbye!")
    except Exception as e:
        print(f" Error starting server: {e}")
        sys.exit(1)
