#!/usr/bin/env python3
"""
Local development server for testing static site
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse


def run_local_server(port: int = 8000, build_dir: str = "build"):
    """Run a local HTTP server for testing"""
    build_path = Path(build_dir)

    if not build_path.exists():
        print(f"Build directory '{build_dir}' does not exist.")
        print("Please run 'python generate_static_data.py' first.")
        return

    print(f"Starting local server at http://localhost:{port}")
    print(f"Serving from: {build_path.absolute()}")
    print("Press Ctrl+C to stop the server")

    try:
        # Change to build directory and start server
        os.chdir(build_path)
        subprocess.run([sys.executable, "-m", "http.server", str(port)])
    except KeyboardInterrupt:
        print("\nServer stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Local development server for werewolf visualization"
    )
    parser.add_argument(
        "--port", "-p", type=int, default=8000, help="Port to serve on (default: 8000)"
    )
    parser.add_argument(
        "--build-dir",
        "-d",
        default="build",
        help="Build directory to serve (default: build)",
    )
    parser.add_argument(
        "--rebuild",
        "-r",
        action="store_true",
        help="Rebuild static data before serving",
    )

    args = parser.parse_args()

    if args.rebuild:
        print("Rebuilding static data...")
        result = subprocess.run(
            [
                sys.executable,
                "generate_static_data.py",
                "--clean",
                "--output",
                args.build_dir,
            ]
        )
        if result.returncode != 0:
            print("Build failed!")
            return
        print("Build completed!")

    run_local_server(args.port, args.build_dir)


if __name__ == "__main__":
    main()
