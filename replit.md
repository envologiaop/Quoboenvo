# Telegram Userbot with Auto-Quote Functionality

## Overview

This project is a Telegram userbot built with Pyrogram that provides auto-quote functionality through integration with @QuotLyBot. The application is designed to run on Render hosting platform with a Flask wrapper to meet web service requirements. The bot can automatically quote messages and manage quote styling with different color options.

## System Architecture

The application follows a dual-service architecture:

1. **Flask Web Server**: Provides HTTP endpoints for health checks and status monitoring, required for Render deployment
2. **Pyrogram Userbot**: Handles Telegram API interactions and auto-quote functionality
3. **State Management**: JSON file-based persistence for userbot settings
4. **Configuration Management**: Environment variable-based configuration with validation

## Key Components

### 1. Configuration Management (`config.py`)
- **Purpose**: Centralized configuration handling for Telegram API credentials
- **Key Features**:
  - Environment variable loading with dotenv support
  - Configuration validation to ensure required credentials are present
  - Type conversion for API_ID (integer validation)
- **Design Decision**: Used environment variables for security and deployment flexibility

### 2. Main Application (`main.py`)
- **Purpose**: Entry point that orchestrates both Flask web server and Telegram userbot
- **Architecture**: Multi-threaded approach with Flask running in separate thread
- **Design Decision**: Flask wrapper chosen to meet Render's web service requirements while maintaining userbot functionality

### 3. Userbot Core (`userbot.py`)
- **Purpose**: Core Telegram userbot functionality using Pyrogram
- **Key Features**:
  - Auto-quote mode toggle
  - Color management for quotes
  - State persistence
  - Error handling with logging to Saved Messages
- **Design Decision**: Pyrogram chosen over other libraries for its async support and user account capabilities

### 4. State Management (`state.json`)
- **Purpose**: Persistent storage for userbot settings
- **Structure**: Simple JSON format storing auto-quote status and current color
- **Design Decision**: File-based storage chosen for simplicity, suitable for single-instance deployment

## Data Flow

1. **Initialization**:
   - Configuration loaded from environment variables
   - State restored from JSON file
   - Both Flask server and userbot client initialized

2. **Message Processing**:
   - Incoming messages filtered and processed by userbot
   - Auto-quote functionality triggered based on current state
   - Integration with @QuotLyBot for quote generation

3. **State Updates**:
   - Changes to auto-quote mode or color settings
   - Immediate persistence to JSON file
   - Real-time status available through Flask endpoints

## External Dependencies

### Core Dependencies
- **Pyrogram**: Telegram client library for userbot functionality
- **Flask**: Web framework for HTTP endpoints
- **python-dotenv**: Environment variable management

### Telegram API Integration
- **Telegram API**: Direct integration using API_ID and API_HASH
- **@QuotLyBot**: Third-party bot for quote generation and styling
- **Session String**: Persistent authentication for user account access

## Deployment Strategy

### Render Platform Deployment
- **Web Service**: Flask server provides required HTTP interface
- **Environment Variables**: Secure credential management
- **Port Configuration**: Dynamic port assignment from Render
- **Health Checks**: Dedicated endpoints for service monitoring

### Configuration Requirements
- `API_ID`: Telegram API application ID
- `API_HASH`: Telegram API application hash
- `SESSION_STRING`: Pyrogram session string for authentication
- `PORT`: Web server port (automatically set by Render)

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

```
Changelog:
- July 04, 2025. Initial setup
```