"""
Start from scratch here. Aim at having a facility that runs end-to-end.
"""
import json
import re
from pprint import pprint
from pathlib import Path
from typing import List, Optional
from serpapi import GoogleSearch

# Fixed parameters
ITEM_PER_PAGE: int = 20  # This is fixed
SERP_API_KEY: str = Path('serp_api_key').read_text()


class CitationRetriever:
    def __init__(self, article_id: int, citation_records_dir: str):
        self._article_id: int = article_id
        self._citation_records_dir = citation_records_dir
        # The rest will be initialize when running self.get_full_list_of_results().
        self._organic_results = []
        self._num_of_pages: Optional[int] = None
        self._num_of_citations: Optional[int] = None

    def get_results_per_page(self, start: int) -> dict:
        params = {
            "engine": "google_scholar",     # engine name
            "cites": self._article_id,                 # article_id
            "api_key": SERP_API_KEY,        # SERP API
            "num": start + ITEM_PER_PAGE,   # read till
            "start": start}                 # start position
        search = GoogleSearch(params)
        results = search.get_dict()
        return results

    @property
    def num_of_pages(self) -> int:
        if self._num_of_pages is None:
            raise ValueError("Number of pages is not known yet!")
        return self._num_of_pages

    @property
    def num_of_citations(self) -> int:
        self._num_of_citations = len(self.organic_results)
        if self._num_of_citations == 0:
            raise ValueError("Number of citations is not known yet!")
        return self._num_of_citations

    @property
    def output_json_filename(self) -> str:
        return f"{self._citation_records_dir}/{self._article_id}_{self.num_of_citations}citations.json"

    @property
    def organic_results(self) -> List[dict]:
        if len(self._organic_results) == 0:
            self.get_full_list_of_results()
        return self._organic_results

    def get_full_list_of_results(self):
        """
        Procedure to get full list of citation results
        """
        # Retrieve on first page the total number of pages
        first_page_results = self.get_results_per_page(start=0)
        if 'pagination' in first_page_results:
            self._num_of_pages = max([int(x) for x in first_page_results['pagination']['other_pages'].keys()])
        else:
            self._num_of_pages = 1
        self._organic_results = self._organic_results + first_page_results['organic_results']
        print(f"Total number of pages: {self._num_of_pages}.")

        if self.num_of_pages > 1:
            for start_position in range(1, self.num_of_pages):
                page_results = self.get_results_per_page(start=start_position*ITEM_PER_PAGE)
                self._organic_results = self._organic_results + page_results['organic_results']
        print(f"In total, {self.num_of_citations} citations is retrieved for article {self._article_id}.")

    def dump_full_list_of_results_to_json(self):
        with open(self.output_json_filename, 'w', encoding='utf8') as json_file:
            json.dump(self.organic_results, json_file, ensure_ascii=False, indent=2)
        print(f"Citation records are dumped to JSON file: '{self.output_json_filename}'.")


class Author:
    def __init__(self, name, link, serpapi_scholar_link, author_id):
        self._name = name
        self._link = link
        self._serpapi_scholar_link = serpapi_scholar_link
        self._author_id = author_id

    @classmethod
    def from_dict(cls, author_dict: dict):
        return cls(
            name=author_dict['name'],
            link=author_dict['link'],
            serpapi_scholar_link=author_dict['serpapi_scholar_link'],
            author_id=author_dict['author_id'])

    @property
    def name(self):
        return self._name

    @property
    def link(self):
        return self._link

    @property
    def serpapi_scholar_link(self):
        return self._serpapi_scholar_link

    @property
    def author_id(self):
        return self._author_id


class Citation:
    """
    TODO: use some other ways to retrieve author information
    """
    def __init__(self, title: str, result_id: str, link: str, publication_info: dict):
        self._title = title
        self._result_id = result_id
        self._link = link
        self._publication_info = publication_info
        self._authors = self.get_authors()

    def __str__(self):
        compiled_str = \
            f"""
            Title: {self.title}
            Result ID: {self.result_id}
            URL: {self.link}
            Authors: {self.authors_to_str}

            """
        return compiled_str

    def get_authors(self) -> Optional[List[Author]]:
        if self._publication_info.get('authors', None):
            return [Author.from_dict(author_dict) for author_dict in self._publication_info['authors']]
        return None

    @classmethod
    def from_dict(cls, citation_dict: dict):
        return cls(
            title=citation_dict['title'],
            result_id=citation_dict['result_id'],
            link=citation_dict.get('link', ""),
            publication_info=citation_dict['publication_info'])

    @property
    def title(self):
        return self._title

    @property
    def result_id(self):
        return self._result_id

    @property
    def link(self):
        return self._link

    @property
    def publication_info(self):
        return self._publication_info

    @property
    def authors(self) -> list:
        """TODO: string method for authors"""
        return self._authors

    @property
    def authors_to_str(self) -> str:
        if self.authors:
            author_str = ', '.join([x.name for x in self.authors])
        else:
            author_str = 'AUTHORS'
        return author_str


class CitationManager:
    """
    Manage citation records per article using pandas.
    Export a CSV file with the following columns:
        Exclude, Authors, Title, URL, Year, Result ID, Quotes, Detail usage, Relationship, Access

    """
    def __init__(self, article_id: int, citation_records_dir: str, json_file: Optional[str] = None):
        self._article_id = article_id
        self._citation_records_dir = citation_records_dir
        if json_file:
            # *** Test with offline file first ***
            with open(json_file, "r") as f:
                self._organic_results = json.load(f)
            pprint(self._organic_results)
            self._output_tsv_filename = re.sub(".json", ".tsv", json_file)
        else:
            # *** Use Serp API ***
            self._citation_retriever = CitationRetriever(
                article_id=self.article_id, citation_records_dir=self._citation_records_dir)
            self._organic_results = self._citation_retriever.organic_results
            self._citation_retriever.dump_full_list_of_results_to_json()  # Optional
            self._output_tsv_filename = re.sub(".json", ".tsv", self._citation_retriever.output_json_filename)
        self._citations = [Citation.from_dict(citation_dict=x) for x in self._organic_results]


    @property
    def output_tsv_filename(self) -> str:
        return self._output_tsv_filename

    @property
    def article_id(self):
        return self._article_id

    @property
    def citations(self):
        return self._citations

    def output_citations(self):

        with open(self.output_tsv_filename, "w") as f:
            for citation in self._citations:
                output_tuple = (citation.title, citation.result_id, citation.link, citation.authors_to_str)
                f.write('\t'.join(output_tuple)+'\n')
                print(str(citation))
        print(f"Finished writing file {self.output_tsv_filename}")

