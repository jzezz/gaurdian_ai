import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.run import run_cli

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Guardian AI benchmark suite")
    parser.add_argument("--dataset", type=str, default=None,
                        help="Optional folder of real images with a benign/ subfolder")
    args = parser.parse_args()

    run_cli(folder_dataset=args.dataset)
