import json
from typing import List, Union, Dict
from exporters.base_exporter import BaseExporter
from models.repository import RepositoryData
from setup.config import OUTPUT_ENCODING

class JSONExporter(BaseExporter):
    """Data exporter for JSON format"""
    
    def export(self, repositories: Union[List[RepositoryData], List[Dict]]) -> None:
        """Exports repositories to JSON - accepts RepositoryData or dict"""
        if not repositories:
            print("⚠️ No repositories to export to JSON.")
            return
        
        print(f"📄 Exporting {len(repositories)} repositories to {self.output_file}...")
        
        try:
            # Convert only if it's a RepositoryData object
            data_to_export = []
            for repo in repositories:
                if isinstance(repo, dict):
                    # It's already a dict, use it directly
                    data_to_export.append(repo)
                else:
                    # It's a RepositoryData object, convert it to a dict
                    data_to_export.append(repo.to_dict())
            
            with open(self.output_file, 'w', encoding=OUTPUT_ENCODING) as f:
                json.dump(data_to_export, f, ensure_ascii=False, indent=2)
            
            print(f"✅ JSON exported to {self.output_file}")
            
        except Exception as e:
            print(f"⚠️ Error exporting JSON: {e}")
            raise