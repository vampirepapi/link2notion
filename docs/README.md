# LinkedMash Documentation

Welcome to the LinkedMash documentation directory. This folder contains design documents, architectural decisions, and future planning materials for the LinkedMash project.

## Documents

### [LinkedMash Design Document v1.0](./linkedmash_design_document_v1.md)
Complete specification for the next-generation LinkedMash platform. This document outlines the vision for a full-stack, multi-user SaaS application with advanced features including:
- Multi-user architecture with PostgreSQL storage
- AI-powered chat and auto-labeling
- Multiple export destinations (Notion, Google Sheets, Airtable)
- Vector search and semantic querying
- Scheduled auto-sync and background jobs

**Status**: Future vision / Long-term roadmap
**Tech Stack**: Next.js 14, TypeScript, PostgreSQL, Redis, Pinecone
**Purpose**: Serves as the north star for product evolution and provides a complete blueprint for implementing the enterprise-grade version

## Current Implementation

The current repository contains a Python-based MVP that provides core functionality:
- LinkedIn saved post scraping (Playwright)
- Notion export
- Markdown export
- Streamlit web UI
- CLI interface

See the main [README.md](../README.md) for usage instructions.

## How These Documents Relate

The design document represents the **long-term vision** for LinkedMash as a production SaaS product. The current implementation is a **functional MVP** that validates the core concept and serves real user needs today.

Think of it as:
- **Current**: Proof of concept with essential features
- **Design Doc v1.0**: Production-ready, scalable, monetizable platform

## For Contributors

If you're interested in contributing:

**Short-term** (Current Python codebase):
- Bug fixes and improvements to existing features
- Documentation updates
- Additional export formats
- UI/UX enhancements to Streamlit interface

**Long-term** (Design Doc v1.0):
- Help plan the architecture
- Prototype new features
- Research AI integration approaches
- Design the data migration strategy

## Questions?

Open an issue on GitHub to discuss features, architecture decisions, or contribute ideas to the design document.
