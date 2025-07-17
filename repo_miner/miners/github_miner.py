import json
import shutil
import time
import os
import glob
from typing import Dict, List, Optional

from services.repository_service import RepositoryService
from services.issue_service import IssueService
from services.pull_request_service import PullRequestService
from models.repository import RepositoryData
from exporters.csv_exporter import CSVExporter
from cache.progress_manager import ProgressManager
from setup.config import (
    SEARCH_LANGUAGE, MIN_STARS, MAX_ISSUE_CLOSE_DAYS,
    OUTPUT_FILE, OUTPUT_ENCODING, EXPORT_FORMAT, CSV_OUTPUT_FILE,
    BATCH_SIZE, TOTAL_TARGET_REPOS
)

class GitHubMiner:
    """
    Main class for mining GitHub repositories.
    It operates in batches, fetching more data on demand when the cache is exhausted.
    """

    def __init__(self):
        self.repo_service = RepositoryService()
        self.issue_service = IssueService()
        self.pr_service = PullRequestService()
        self.progress_manager = ProgressManager()

    def mine_repositories(self) -> None:
        """
        Executes ONE mining SESSION, automatically fetching more repositories
        if the current cache is exhausted.
        """
        print(f"🚀 Starting a mining session for {SEARCH_LANGUAGE.upper()} repositories...")

        config_params = self._get_config_params()
        config_hash = self.progress_manager.get_config_hash(config_params)
        stats = self.progress_manager.get_statistics()

        if stats['total_processed'] >= TOTAL_TARGET_REPOS:
            print(f"✅ Target of {TOTAL_TARGET_REPOS} repositories already reached!")
            self._save_final_results()
            return

        start_time = time.time()

        try:
            start_index = self.progress_manager.get_next_start_index(BATCH_SIZE)
            repos = self._ensure_sufficient_repo_cache(config_hash, start_index)

            if not repos or start_index >= len(repos):
                print("\n✅ No more repositories to process at the moment.")
                self._finalize_execution(start_time)
                return

            end_index = min(start_index + BATCH_SIZE, len(repos))
            self._show_progress_info(start_index, end_index)
            self._process_batch(repos, start_index, end_index)

        finally:
            self._finalize_execution(start_time)

    def _ensure_sufficient_repo_cache(self, config_hash: str, start_index: int) -> List[Dict]:
        """
        Checks the repository cache and fetches more if necessary, bypassing
        the API's 1000-result limit.
        """
        repos = self.progress_manager.get_search_results(config_hash) or []

        if start_index < len(repos):
            print("✅ Repository cache is sufficient for the next batch.")
            return repos

        print("\n" + "="*50)
        print(f"🧠 Cache exhausted (Index: {start_index}, Cache: {len(repos)}).")
        print("   Fetching more repositories from the GitHub API...")
        print("="*50 + "\n")

        # Determine the star ceiling for the next search to get a new set of results.
        max_stars_for_next_search = None
        if repos:
            # Get the star count from the last repository in the cache (the one with the fewest stars).
            last_repo_in_cache = repos[-1]
            max_stars_for_next_search = last_repo_in_cache.get('stargazers_count')

        # Call the search service, passing the star ceiling.
        new_repos = self.repo_service.search_repositories_adaptive(
            max_stars=max_stars_for_next_search
        )

        if not new_repos:
            print("❌ The search returned no new repositories. End of process.")
            return repos

        # Add only the repositories that are not already in the cache.
        existing_names = {repo['full_name'] for repo in repos}
        unique_new = [r for r in new_repos if r['full_name'] not in existing_names]

        if not unique_new:
            print("⚠️ The new search did not return unique repositories. The cache will not be expanded.")
            return repos

        repos.extend(unique_new)
        self.progress_manager.save_search_results(repos, config_hash)
        print(f"   ✅ Cache expanded to {len(repos)} repositories.")
        return repos

    def _get_config_params(self) -> Dict:
        """Returns configuration parameters for hashing."""
        return {
            'language': SEARCH_LANGUAGE,
            'min_stars': MIN_STARS,
            'max_issue_close_days': MAX_ISSUE_CLOSE_DAYS,
            'total_target_repos': TOTAL_TARGET_REPOS
        }

    def _show_progress_info(self, start_index: int, end_index: int) -> None:
        """Shows progress information."""
        stats = self.progress_manager.get_statistics()
        print(f"\n📊 Automatic progress detected:")
        print(f"   ✅ Already accepted: {stats['total_processed']}")
        print(f"   ❌ Rejected: {stats['total_rejected']}")
        print(f"   🔄 Resuming from index: {start_index}")
        print(f"   🎯 Processing batch: {start_index} to {end_index-1}")

    def _process_batch(self, repos: List[Dict], start_index: int, end_index: int) -> None:
        """Processes a batch of repositories."""
        batch_to_process = repos[start_index:end_index]
        print(f"📦 Processing {len(batch_to_process)} repositories...")

        batch_accepted_data = []
        for i, repo_json in enumerate(batch_to_process):
            current_index = start_index + i
            print(f"\n[{current_index+1}/{len(repos)}] Analyzing: {repo_json['full_name']}")

            repo_data = self._process_repository(repo_json)
            rejected_list = []

            if repo_data:
                batch_accepted_data.append(repo_data.to_dict())
                print("  ✅ ACCEPTED - Meets all criteria.")
            else:
                rejected_list.append(repo_json['full_name'])

            self.progress_manager.update_progress(repo_data, rejected_list, current_index + 1)

        print(f"\n📊 BATCH COMPLETE: {len(batch_accepted_data)}/{len(batch_to_process)} repositories accepted.")
        self._save_batch_results(start_index, batch_accepted_data)
        self._show_next_steps()

    def _process_repository(self, repo: dict) -> Optional[RepositoryData]:
        """Processes a single repository, returning a RepositoryData object or None."""
        prs_data = self.pr_service.get_pr_comparison_data(repo['full_name'])
        if not prs_data:
            print("  ✘ No valid PRs or insufficient data.")
            return None
        print(f"  ✓ Valid PRs found: {len(prs_data)}")

        avg_days = self.issue_service.get_avg_issue_close_time(repo['full_name'])
        if avg_days is None:
            print("  ✘ Not enough closed issues for calculation.")
            return None
        print(f"  ✓ Average issue close time: {avg_days:.2f} days")

        if avg_days >= MAX_ISSUE_CLOSE_DAYS:
            print(f"  ✘ Rejected - Average time too high ({avg_days:.2f} >= {MAX_ISSUE_CLOSE_DAYS} days).")
            return None

        languages = self.repo_service.get_repository_languages(repo['full_name'])
        dominant_language = max(languages.items(), key=lambda item: item[1])[0] if languages else None

        return RepositoryData(
            name=repo['full_name'], url=repo['html_url'], stars=repo['stargazers_count'],
            watchers=repo.get('watchers_count', 0), forks=repo.get('forks_count', 0),
            created_at=repo['created_at'], updated_at=repo['updated_at'],
            avg_issue_close_days=avg_days, prs=prs_data, default_branch=repo['default_branch'],
            languages=languages, dominant_language=dominant_language
        )

    def _save_batch_results(self, start_index: int, batch_repos: List[Dict]) -> None:
        """Saves the results of a batch to JSON and CSV files."""
        batch_number = (start_index // BATCH_SIZE) + 1
        print(f"💾 SAVING BATCH {batch_number:03d}:")

        batches_dir = os.path.join("results", "batches")
        os.makedirs(batches_dir, exist_ok=True)

        json_file = os.path.join(batches_dir, f"batch_{batch_number:03d}_{OUTPUT_FILE}")
        csv_file = os.path.join(batches_dir, f"batch_{batch_number:03d}_{CSV_OUTPUT_FILE}")

        if EXPORT_FORMAT.lower() in ['json', 'both']:
            with open(json_file, 'w', encoding=OUTPUT_ENCODING) as f:
                json.dump(batch_repos, f, ensure_ascii=False, indent=2)
            print(f"   ✅ JSON saved: {json_file} ({len(batch_repos)} repositories)")

        if EXPORT_FORMAT.lower() in ['csv', 'both']:
            CSVExporter(csv_file).export(batch_repos)
            print(f"   ✅ CSV saved: {csv_file} ({len(batch_repos)} repositories)")

    def _save_final_results(self) -> None:
        """Consolidates all batches into final files and cleans up."""
        print("\n" + "="*50)
        print("💾 Consolidating all batches into final files...")
        
        batches_dir = os.path.join("results", "batches")
        final_dir = os.path.join("results", "final")
        os.makedirs(final_dir, exist_ok=True)

        batch_pattern = os.path.join(batches_dir, f"batch_*_{OUTPUT_FILE}")
        batch_files = sorted(glob.glob(batch_pattern))

        if not batch_files:
            print("⚠️ No batch files found to consolidate.")
            return

        all_repos = []
        for batch_file in batch_files:
            with open(batch_file, 'r', encoding=OUTPUT_ENCODING) as f:
                all_repos.extend(json.load(f))

        print(f"📁 {len(batch_files)} batches found, totaling {len(all_repos)} repositories.")

        final_json_file = os.path.join(final_dir, OUTPUT_FILE)
        final_csv_file = os.path.join(final_dir, CSV_OUTPUT_FILE)

        if EXPORT_FORMAT.lower() in ['json', 'both']:
            with open(final_json_file, 'w', encoding=OUTPUT_ENCODING) as f:
                json.dump(all_repos, f, ensure_ascii=False, indent=2)
            print(f"✅ Final JSON saved: {final_json_file}")

        if EXPORT_FORMAT.lower() in ['csv', 'both']:
            CSVExporter(final_csv_file).export(all_repos)
            print(f"✅ Final CSV saved: {final_csv_file}")

        # Delete the batches directory after consolidation
        try:
            if os.path.isdir(batches_dir):
                print(f"\n🧹 Cleaning up batch files...")
                shutil.rmtree(batches_dir)
                print(f"   ✅ Batch directory '{batches_dir}' deleted successfully.")
        except Exception as e:
            print(f"   ⚠️ Could not delete batch directory '{batches_dir}': {e}")

    def _show_next_steps(self) -> None:
        """Shows suggested next steps to the user."""
        stats = self.progress_manager.get_statistics()
        if stats['total_processed'] < TOTAL_TARGET_REPOS:
            print("\n" + "-"*50)
            print(f"🔄 To continue, run again: python main.py")
            print(f"   Current progress: {stats['total_processed']}/{TOTAL_TARGET_REPOS} repositories processed.")
        else:
            print("\n🎉 MINING COMPLETE!")
            print(f"   Target reached: {stats['total_processed']}/{TOTAL_TARGET_REPOS} repositories.")
            self._save_final_results()

    def _finalize_execution(self, start_time: float) -> None:
        """Finalizes the execution, saves progress, and shows statistics."""
        elapsed = time.time() - start_time
        print(f"\n⏱️ Time for this session: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        self.repo_service.finalize()
        self.progress_manager.finalize()

    def get_execution_summary(self) -> Dict:
        """Returns an execution summary."""
        stats = self.progress_manager.get_statistics()
        stats['config'] = self._get_config_params()
        return stats