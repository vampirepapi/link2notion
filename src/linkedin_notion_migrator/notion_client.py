"""Notion API client for creating pages."""

import logging
from typing import Dict, List, Optional

import requests

from .config import NotionPropertyConfig
from .models import SavedPost


logger = logging.getLogger(__name__)


class NotionClient:
    """Client for interacting with the Notion API."""

    NOTION_API_BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, api_key: str, database_id: str, properties: NotionPropertyConfig):
        """Initialize the Notion client."""
        self.api_key = api_key
        self.database_id = database_id
        self.properties = properties
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Notion-Version": self.NOTION_VERSION,
                "Content-Type": "application/json",
            }
        )
        self.database_properties = self._fetch_database_properties()

    def _fetch_database_properties(self) -> Dict[str, Dict]:
        """Fetch the database properties from Notion."""
        url = f"{self.NOTION_API_BASE_URL}/databases/{self.database_id}"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("properties", {})

    def create_page(self, post: SavedPost) -> Optional[str]:
        """Create a Notion page for a LinkedIn post."""
        logger.info(f"Creating Notion page for post: {post.to_summary()}")

        url = f"{self.NOTION_API_BASE_URL}/pages"

        properties = self._build_properties(post)
        children = self._build_children(post)

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
            "children": children,
        }

        response = self.session.post(url, json=payload)

        try:
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to create Notion page: {str(e)} - Response: {response.text}")
            return None

        notion_page_id = response.json().get("id")
        logger.info(f"Successfully created Notion page with id: {notion_page_id}")
        return notion_page_id

    def _build_properties(self, post: SavedPost) -> Dict[str, Dict]:
        """Build Notion database properties payload."""
        properties = {}

        title_property = self.properties.title
        if title_property in self.database_properties:
            properties[title_property] = {
                "title": [
                    {
                        "text": {
                            "content": post.content[:200] if post.content else "LinkedIn Saved Post",
                        }
                    }
                ]
            }

        if post.author and self.properties.author in self.database_properties:
            properties[self.properties.author] = {
                "rich_text": [
                    {
                        "text": {
                            "content": post.author,
                        }
                    }
                ]
            }

        if post.url and self.properties.url in self.database_properties:
            properties[self.properties.url] = {"url": post.url}

        if post.posted_at and self.properties.posted_at in self.database_properties:
            properties[self.properties.posted_at] = {
                "date": {
                    "start": post.posted_at.isoformat(),
                }
            }

        if post.saved_at and self.properties.saved_at in self.database_properties:
            properties[self.properties.saved_at] = {
                "date": {
                    "start": post.saved_at.isoformat(),
                }
            }

        if post.urn and self.properties.urn in self.database_properties:
            properties[self.properties.urn] = {
                "rich_text": [
                    {
                        "text": {
                            "content": post.urn,
                        }
                    }
                ]
            }

        if post.content and self.properties.content in self.database_properties:
            properties[self.properties.content] = {
                "rich_text": [
                    {
                        "text": {
                            "content": post.content,
                        }
                    }
                ]
            }

        return properties

    def _build_children(self, post: SavedPost) -> List[Dict]:
        """Build Notion blocks for the page content."""
        children = []

        if post.content:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": post.content,
                                },
                            }
                        ]
                    },
                }
            )

        if post.url:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Original Post",
                                    "link": {
                                        "url": post.url,
                                    },
                                },
                            }
                        ]
                    },
                }
            )

        if post.author:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Author: {post.author}",
                                },
                            }
                        ]
                    },
                }
            )

        if post.posted_at:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Date Posted: {post.posted_at.isoformat()}",
                                },
                            }
                        ]
                    },
                }
            )

        if post.saved_at:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Saved Date: {post.saved_at.isoformat()}",
                                },
                            }
                        ]
                    },
                }
            )

        return children

    def page_exists(self, urn: str) -> bool:
        """Check if a page with the given URN already exists."""
        if not urn:
            return False

        if self.properties.urn not in self.database_properties:
            return False

        url = f"{self.NOTION_API_BASE_URL}/databases/{self.database_id}/query"

        payload = {
            "filter": {
                "property": self.properties.urn,
                "rich_text": {
                    "equals": urn,
                }
            }
        }

        response = self.session.post(url, json=payload)

        try:
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to query Notion database: {str(e)} - Response: {response.text}")
            return False

        results = response.json().get("results", [])
        return len(results) > 0
