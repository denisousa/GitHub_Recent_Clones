import math
from typing import List, Dict, Any, Optional
from services.github_api import GitHubAPIService
from setup.config import MIN_STARS, SEARCH_LANGUAGE, REPOS_PER_PAGE

class RepositoryService(GitHubAPIService):
    """Service responsible for fetching repositories with an adaptive search"""

    def search_repositories_adaptive(
        self,
        max_stars: Optional[int] = None
    ) -> List[Dict]:
        """
        Searches for repositories adaptively, adjusting the star query
        to bypass the API's 1000-result limit.

        :param max_stars: The maximum number of stars for the search. If provided,
                          the search will be for repositories with stars between MIN_STARS
                          and max_stars - 1.
        """
        if max_stars and max_stars <= MIN_STARS:
            print(f"⚠️ No more repositories to fetch. Star ceiling ({max_stars}) is less than or equal to the minimum ({MIN_STARS}).")
            return []

        # Build the search query based on the star range
        if max_stars:
            # Subsequent search: creates a star window to avoid fetching the same repositories.
            # Ex: stars:50..849
            stars_query = f"stars:{MIN_STARS}..{max_stars - 1}"
            print(f"🧠 ADAPTIVE SEARCH: Continuing search with new star range: {stars_query}")
        else:
            # First search: gets all repositories above the minimum star count.
            stars_query = f"stars:>={MIN_STARS}"
            print(f"🧠 ADAPTIVE SEARCH: Starting search with star range: {stars_query}")

        query = f"language:{SEARCH_LANGUAGE} {stars_query}"

        return self._search_repositories_paginated(query)

    def _search_repositories_paginated(self, query: str) -> List[Dict]:
        """
        Executes the search on the GitHub API, paginating up to the 1000-result limit.
        """
        all_repos = []
        print(f"🔍 Executing search with query: '{query}'")

        # The GitHub search API allows up to 10 pages of 100 results (1000 total)
        for page_num in range(1, 11): # Pages go from 1 to 10
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': REPOS_PER_PAGE,
                'page': page_num
            }
            
            # Use the base class method to make the request
            url = f"{self.base_url}/search/repositories"
            response_data = self.get_json_response(url, params=params)

            # If the response is null or doesn't contain 'items', something went wrong.
            if not response_data or 'items' not in response_data:
                print(f"   ❌ Failed to get results for page {page_num} or end of results.")
                break

            page_repos = response_data['items']
            all_repos.extend(page_repos)
            print(f"   📄 Page {page_num} loaded, {len(page_repos)} repositories found on this page.")

            # If the API returns fewer items than requested, it's the last page.
            if len(page_repos) < REPOS_PER_PAGE:
                print("   ✅ End of results for this query.")
                break
        
        if not all_repos:
            print("   ⚠️ The search returned no repositories for this star range.")

        print(f"✅ Search complete: {len(all_repos)} repositories found in this search session.")
        return all_repos

    def get_repository_languages(self, repo_full_name: str) -> Optional[Dict[str, int]]:
        """Returns the repository's languages with their respective byte counts"""
        try:
            url = f"{self.base_url}/repos/{repo_full_name}/languages"
            return self.get_json_response(url)
        except Exception as e:
            print(f"⚠️ Error getting languages for {repo_full_name}: {e}")
            return None