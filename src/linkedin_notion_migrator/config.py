"""Configuration management for the LinkedIn to Notion migrator."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class NotionPropertyConfig:
    """Configuration for Notion database property names."""
    title: str = "Name"
    author: str = "Author"
    url: str = "Post URL"
    posted_at: str = "Date Posted"
    saved_at: str = "Saved Date"
    content: str = "Content"
    urn: str = "LinkedIn URN"


@dataclass
class Config:
    """Main configuration class for the migrator."""
    linkedin_email: str
    linkedin_password: str
    notion_api_key: str
    notion_database_id: str
    headless: bool = True
    notion_properties: NotionPropertyConfig = None
    
    def __post_init__(self):
        if self.notion_properties is None:
            self.notion_properties = NotionPropertyConfig()
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        linkedin_email = os.getenv("LINKEDIN_EMAIL")
        linkedin_password = os.getenv("LINKEDIN_PASSWORD")
        notion_api_key = os.getenv("NOTION_API_KEY")
        notion_database_id = os.getenv("NOTION_DATABASE_ID")
        
        if not linkedin_email:
            raise ValueError("LINKEDIN_EMAIL environment variable is required")
        if not linkedin_password:
            raise ValueError("LINKEDIN_PASSWORD environment variable is required")
        if not notion_api_key:
            raise ValueError("NOTION_API_KEY environment variable is required")
        if not notion_database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is required")
        
        headless_str = os.getenv("HEADLESS", "true").lower()
        headless = headless_str in ("true", "1", "yes")
        
        notion_properties = NotionPropertyConfig(
            title=os.getenv("NOTION_TITLE_PROPERTY", "Name"),
            author=os.getenv("NOTION_AUTHOR_PROPERTY", "Author"),
            url=os.getenv("NOTION_URL_PROPERTY", "Post URL"),
            posted_at=os.getenv("NOTION_POSTED_AT_PROPERTY", "Date Posted"),
            saved_at=os.getenv("NOTION_SAVED_AT_PROPERTY", "Saved Date"),
            content=os.getenv("NOTION_CONTENT_PROPERTY", "Content"),
            urn=os.getenv("NOTION_URN_PROPERTY", "LinkedIn URN"),
        )
        
        return cls(
            linkedin_email=linkedin_email,
            linkedin_password=linkedin_password,
            notion_api_key=notion_api_key,
            notion_database_id=notion_database_id,
            headless=headless,
            notion_properties=notion_properties,
        )
