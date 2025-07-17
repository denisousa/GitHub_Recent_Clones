import json
import os
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import asdict

class ProgressManager:
    """Manages the mining progress automatically"""
    
    def __init__(self):
        data_dir = ".data"
        os.makedirs(data_dir, exist_ok=True)
        self.progress_file = os.path.join(data_dir, "mining_progress.json")
        self.progress_data = self._load_progress()
    
    def _load_progress(self) -> dict:
        """Loads previous progress"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"📊 Progress loaded: {data.get('total_processed', 0)} repositories processed")
                    return data
            except Exception as e:
                print(f"⚠️ Error loading progress: {e}")
                return self._create_empty_progress()
        return self._create_empty_progress()
    
    def _create_empty_progress(self) -> dict:
        """Creates an empty progress structure"""
        return {
            'total_processed': 0,
            'last_index': 0,
            'processed_repos': [],
            'rejected_repos': [],
            'search_results': [],
            'last_update': None,
            'config_hash': None,
            'current_batch': 0,  # ← NEW: current batch control
            'cache_exhausted': False  # ← NEW: flag for exhausted cache
        }
    
    def get_config_hash(self, config_params: dict) -> str:
        """Generates a hash of the current configuration"""
        config_str = json.dumps(config_params, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def get_next_start_index(self, batch_size: int) -> int:
        """
        Returns the next index to be processed, which is simply
        the last index that was saved.
        """
        last_index = self.progress_data.get('last_index', 0)
        
        print(f"🧠 GETTING NEXT INDEX:")
        print(f"   📍 Last saved index: {last_index}")
        
        # The function now just returns the last index.
        # The logic to decide if more repositories need to be fetched
        # belongs to GitHubMiner, which will compare this index with the
        # current cache size.
        return last_index
    
    def save_search_results(self, repos: List[Dict], config_hash: str):
        """Saves initial search results"""
        existing_repos = self.progress_data.get('search_results', [])
        
        # If expanding an existing cache
        if existing_repos and len(repos) > len(existing_repos):
            print(f"🔍 Expanding cache: {len(existing_repos)} → {len(repos)} repositories")
            self.progress_data['cache_exhausted'] = False  # Reset flag
            # ✅ FIXED: Keep current index if cache expanded
            # Do not reset last_index here
        elif not existing_repos:
            print(f"🔍 New cache created: {len(repos)} repositories")
            self.progress_data['last_index'] = 0  # Reset only for a new cache
            self.progress_data['cache_exhausted'] = False
        
        self.progress_data['search_results'] = repos
        self.progress_data['config_hash'] = config_hash
        self.progress_data['last_update'] = time.time()
        self._save_progress()
        print(f"🔍 Search results saved: {len(repos)} repositories")
    
    def get_search_results(self, config_hash: str) -> Optional[List[Dict]]:
        """Retrieves search results if the config has not changed"""
        if (self.progress_data.get('config_hash') == config_hash and 
            self.progress_data.get('search_results')):
            cache_size = len(self.progress_data['search_results'])
            print(f"🎯 Reusing search results: {cache_size} repos")
            return self.progress_data['search_results']
        return None
    
    def update_progress(self, processed_repo: Optional[Any], rejected_repos: List[str], current_index: int):
        """Updates progress"""
        if processed_repo:
            # Convert to dict if it is a dataclass
            if hasattr(processed_repo, '__dict__'):
                repo_dict = asdict(processed_repo) if hasattr(processed_repo, '__dataclass_fields__') else processed_repo.__dict__
            else:
                repo_dict = processed_repo
            
            self.progress_data['processed_repos'].append(repo_dict)
            self.progress_data['total_processed'] += 1
        
        self.progress_data['rejected_repos'].extend(rejected_repos)
        self.progress_data['last_index'] = current_index
        self.progress_data['last_update'] = time.time()
        
        # ✅ NEW: Check if cache is being exhausted
        cache_size = len(self.progress_data.get('search_results', []))
        if current_index >= cache_size - 10:  # Nearing the end of the cache
            print(f"⚠️ Cache is nearing exhaustion: {current_index}/{cache_size}")
        
        # Save every 5 processed repos
        if self.progress_data['total_processed'] % 5 == 0:
            self._save_progress()
    
    def mark_cache_exhausted(self):
        """Marks cache as exhausted to force a new search"""
        self.progress_data['cache_exhausted'] = True
        print(f"🔄 Cache marked as exhausted")
        self._save_progress()
    
    def reset_index_for_new_search(self):
        """Resets index for a new search"""
        self.progress_data['last_index'] = 0
        self.progress_data['cache_exhausted'] = False
        print(f"🔄 Index reset for new search")
        self._save_progress()
    
    def _save_progress(self):
        """Saves progress to the file"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving progress: {e}")
    
    def get_statistics(self) -> dict:
        """Returns progress statistics"""
        return {
            'total_processed': self.progress_data.get('total_processed', 0),
            'total_rejected': len(self.progress_data.get('rejected_repos', [])),
            'last_index': self.progress_data.get('last_index', 0),
            'search_results_count': len(self.progress_data.get('search_results', [])),
            'cache_exhausted': self.progress_data.get('cache_exhausted', False)
        }
    
    def get_processed_repos(self) -> List[Dict]:
        """Returns all processed repositories"""
        return self.progress_data.get('processed_repos', [])
    
    def finalize(self):
        """Finalizes and saves progress"""
        self._save_progress()
        print(f"💾 Final progress saved: {self.progress_data['total_processed']} repositories processed")
        