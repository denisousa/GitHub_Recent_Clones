import os
from miners import GitHubMiner
from post_processing import DataProcessor
from setup.config import OUTPUT_FILE

def main():
    """Main function that executes the repository mining and post-processing."""
    try:
        # Create an instance of the miner
        miner = GitHubMiner()
        
        # Execute the mining process
        miner.mine_repositories()
        
        # Show the final execution summary
        summary = miner.get_execution_summary()
        print(f"\n📈 EXECUTION SUMMARY:")
        print(f"   🎯 Configuration: {summary['config']['language'].upper()}")
        print(f"   ⭐ Minimum stars: {summary['config']['min_stars']}")
        print(f"   ⏱️ Max days to close issue: {summary['config']['max_issue_close_days']}")
        print(f"   ✅ Processed: {summary['total_processed']}")
        print(f"   ❌ Rejected: {summary['total_rejected']}")
        print(f"   📊 Last index: {summary['last_index']}")

        base_filename, _ = os.path.splitext(OUTPUT_FILE)
        
        data_processor = DataProcessor(base_filename=base_filename)
        
        data_processor.process()

    except KeyboardInterrupt:
        print("\n🛑 Execution interrupted by user.")
        print("💡 Run the script again to continue from where you left off!")
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        print("💡 Check your settings and try again.")
        raise

if __name__ == "__main__":
    main()