from miners import GitHubMiner
from post_processing import PostProcessor

def main():
    """Main function that executes the full repository mining and processing pipeline."""
    try:
        # --- Step 1: Mining ---
        miner = GitHubMiner()
        miner.mine_repositories()
        
        # Show mining summary
        summary = miner.get_execution_summary()
        print("\n📈 MINING EXECUTION SUMMARY:")
        print(f"   🎯 Configuration: {summary['config']['language'].upper()}")
        print(f"   ⭐ Min stars: {summary['config']['min_stars']}")
        print(f"   ⏱️ Max issue close days: {summary['config']['max_issue_close_days']}")
        print(f"   ✅ Accepted: {summary['total_processed']}")
        print(f"   ❌ Rejected: {summary['total_rejected']}")
        print(f"   📊 Last index analyzed: {summary['last_index']}")

        # --- Step 2: Post-Processing ---
        post_processor = PostProcessor()
        
        # Consolidate all generated batches
        if post_processor.consolidate_batches():
            # If consolidation was successful, apply the quality filter
            post_processor.apply_quality_filter()

    except KeyboardInterrupt:
        print("\n🛑 Execution interrupted by the user.")
        print("💡 Run the script again to continue from where you left off!")
    except Exception as e:
        print(f"\n❌ A critical error occurred during execution: {str(e)}")
        print("💡 Check your settings and error logs, then try again.")
        raise

if __name__ == "__main__":
    main()