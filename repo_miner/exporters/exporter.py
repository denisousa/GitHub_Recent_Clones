import json
import csv
from typing import List, Union, Dict
from exporters.base_exporter import BaseExporter
from models.repository import RepositoryData
from setup.config import OUTPUT_ENCODING

class Exporter(BaseExporter):
    """Unified data exporter for JSON and CSV formats."""

    def export(self, repositories: Union[List[RepositoryData], List[Dict]]) -> None:
        """
        Exports repositories to the format specified by the output file extension.
        """
        file_extension = self._get_file_extension()

        if file_extension == 'json':
            self._export_to_json(repositories)
        elif file_extension == 'csv':
            self._export_to_csv(repositories)
        else:
            print(f"⚠️ Unsupported export format for extension: '{file_extension}'. Please use 'json' or 'csv'.")

    def _export_to_json(self, repositories: Union[List[RepositoryData], List[Dict]]) -> None:
        """Exports repositories to JSON - accepts RepositoryData or dict"""
        if not repositories:
            print("⚠️ No repositories to export to JSON.")
            return
        
        print(f"📄 Exporting {len(repositories)} repositories to {self.output_file}...")
        
        try:
            data_to_export = []
            for repo in repositories:
                if isinstance(repo, dict):
                    data_to_export.append(repo)
                else:
                    data_to_export.append(repo.to_dict())
            
            with open(self.output_file, 'w', encoding=OUTPUT_ENCODING) as f:
                json.dump(data_to_export, f, ensure_ascii=False, indent=2)
            
            print(f"✅ JSON exported to {self.output_file}")
            
        except Exception as e:
            print(f"⚠️ Error exporting JSON: {e}")
            raise

    def _export_to_csv(self, repositories: Union[List[RepositoryData], List[Dict]]) -> None:
        """Exports repositories to CSV - accepts RepositoryData or dict"""
        if not repositories:
            print("⚠️ No repositories to export to CSV.")
            return
        
        print(f"📊 Exporting {len(repositories)} repositories to {self.output_file}...")
        
        with open(self.output_file, 'w', newline='', encoding=OUTPUT_ENCODING) as csvfile:
            fieldnames = [
                'name', 'url', 'stars', 'watchers', 'forks',
                'created_at', 'updated_at', 'avg_issue_close_days',
                'default_branch', 'dominant_language', 'total_prs',
                'total_commits', 'pr_titles'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for repo in repositories:
                try:
                    if isinstance(repo, dict):
                        repo_dict = repo
                        prs = repo_dict.get('prs', [])
                        pr_titles = '; '.join([pr.get('pr_title', '') for pr in prs])
                        total_commits = sum(len(pr.get('commits', [])) for pr in prs)
                    else:
                        repo_dict = repo.__dict__
                        pr_titles = '; '.join([pr.pr_title for pr in repo.prs])
                        total_commits = sum(len(pr.commits) for pr in repo.prs)
                    
                    row = {
                        'name': repo_dict.get('name'),
                        'url': repo_dict.get('url'),
                        'stars': repo_dict.get('stars'),
                        'watchers': repo_dict.get('watchers'),
                        'forks': repo_dict.get('forks'),
                        'created_at': repo_dict.get('created_at'),
                        'updated_at': repo_dict.get('updated_at'),
                        'avg_issue_close_days': round(repo_dict.get('avg_issue_close_days', 0), 2),
                        'default_branch': repo_dict.get('default_branch'),
                        'dominant_language': repo_dict.get('dominant_language'),
                        'total_prs': len(repo_dict.get('prs', [])),
                        'total_commits': total_commits,
                        'pr_titles': pr_titles
                    }
                    
                    writer.writerow(row)
                    
                except Exception as e:
                    print(f"⚠️ Error processing repository: {e}")
                    continue
        
        print(f"✅ CSV exported to {self.output_file}")