from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from webscout import WEBS
from abc import ABC, abstractmethod

@dataclass
class NewsArticle:
    """Data class to store news article information"""
    title: str
    date: str
    source: str
    body: str
    url: str

class NewsFormatter(ABC):
    """Abstract base class for news formatting"""
    @abstractmethod
    def format_article(self, article: NewsArticle, index: int) -> str:
        pass

class DefaultNewsFormatter(NewsFormatter):
    """Default implementation of news formatting"""
    def format_article(self, article: NewsArticle, index: int) -> str:
        return (
            f"{index}. {article.title}\n"
            f"Date: {article.date}\n"
            f"Source: {article.source}\n"
            f"{article.body}\n"
            f"Read more: {article.url}"
        )

class NewsService:
    """Main service class for handling news operations"""
    def __init__(self, max_results: int = 3, formatter: NewsFormatter = DefaultNewsFormatter()):
        self.formatter = formatter
        self.max_results: int = max_results

    def _parse_news_item(self, item: Any) -> Optional[NewsArticle]:
        """Parse a news item into a NewsArticle object"""
        try:
            if isinstance(item, str):
                data = json.loads(item)
            else:
                data = item

            return NewsArticle(
                title=data.get('title', 'No title'),
                date=data.get('date', 'No date'),
                source=data.get('source', 'No source'),
                body=data.get('body', 'No content available'),
                url=data.get('url', 'No URL available')
            )
        except json.JSONDecodeError:
            return None
        except Exception:
            return None

    def get_news(self, topic: str) -> str:
        """
        Fetch and format news for a given topic
        
        Args:
            topic (str): The news topic to search for
            
        Returns:
            str: Formatted news results or error message
        """
        if not topic:
            return "Please provide a news topic."

        try:
            with WEBS() as webs:
                news_results = webs.news(topic, max_results=self.max_results)
            if not news_results:
                return f"No news found for {topic}."

            formatted_results: List[str] = []
            
            for index, result in enumerate(news_results, 1):
                article = self._parse_news_item(result)
                if article:
                    formatted_article = self.formatter.format_article(article, index)
                    formatted_results.append(formatted_article)
                else:
                    formatted_results.append(f"{index}. Error processing news item")

            return "\n\n".join(formatted_results)

        except Exception as e:
            return f"Error fetching news: {str(e)}"


# Example usage
if __name__ == "__main__":
    from rich import print
    result = NewsService(5).get_news("latest ai news")
    for r in result:print(r, end="", flush=True)