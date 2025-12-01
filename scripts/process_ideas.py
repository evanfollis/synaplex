#!/usr/bin/env python3
"""
Process ideas world: Run a tick to process markdown ideas through Synaplex.

This script:
1. Bootstraps the ideas world
2. Runs one or more ticks
3. Agents process ideas from markdown files
4. Manifolds evolve

Usage:
    python scripts/process_ideas.py [--ticks N] [--ideas-dir path] [--store-root path]
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from synaplex.worlds.ideas_world.bootstrap import bootstrap_ideas_world


def main():
    parser = argparse.ArgumentParser(description="Process ideas through Synaplex Ideas World")
    parser.add_argument(
        "--ticks",
        type=int,
        default=1,
        help="Number of ticks to run (default: 1)",
    )
    parser.add_argument(
        "--ideas-dir",
        type=str,
        default="docs/ideas",
        help="Directory containing idea markdown files (default: docs/ideas)",
    )
    parser.add_argument(
        "--store-root",
        type=str,
        default="manifolds/ideas_world",
        help="Root directory for manifold storage (default: manifolds/ideas_world)",
    )
    parser.add_argument(
        "--world-id",
        type=str,
        default="ideas-world",
        help="World identifier (default: ideas-world)",
    )
    
    args = parser.parse_args()
    
    print(f"=== Ideas World Processing ===")
    print(f"Ideas directory: {args.ideas_dir}")
    print(f"Manifold store: {args.store_root}")
    print(f"Ticks: {args.ticks}\n")
    
    # Bootstrap world
    try:
        runtime = bootstrap_ideas_world(
            ideas_dir=args.ideas_dir,
            manifold_store_root=args.store_root,
            world_id=args.world_id,
        )
        print(f"Bootstrapped world with {len(runtime.get_agents())} agents\n")
    except Exception as e:
        print(f"Error bootstrapping world: {e}")
        return 1
    
    # Run ticks
    for tick in range(args.ticks):
        print(f"--- Running tick {tick} ---")
        try:
            runtime.tick(tick)
            print(f"✓ Tick {tick} complete")
        except Exception as e:
            print(f"Error in tick {tick}: {e}")
            return 1
    
    print("\n=== Processing Complete ===")
    print(f"\nManifolds updated in: {args.store_root}")
    print("Inspect manifold files to see how agents have evolved their worldviews.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

