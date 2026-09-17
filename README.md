# Incredibles — Advanced Discord Utility & Music Bot

Incredibles is a high-performance, modular Discord bot built with Python and Nextcord, designed to provide a professional server-management experience alongside a reliable, feature-rich music system.

The project focuses on moderation, server utilities, automated systems, logging, and high-quality music playback, with particular emphasis on reliability and third-party library compatibility.

---

## Highlights

* **Advanced Moderation** — Comprehensive tools for managing and protecting Discord servers.
* **Full Music System** — Queue management, looping, autoplay, volume control, and interactive playback controls.
* **Custom Wavelink Patch** — Resolved compatibility issues between Wavelink 3.4.1 and Lavalink 4.2.2 by patching the missing `channelId` field.
* **YouTube OAuth Support** — Integrated OAuth authentication into the YouTube plugin configuration to improve playback reliability.
* **Advanced Logging** — Tracks server activity across multiple dedicated logging categories.
* **Modular Architecture** — Organized command and system structure designed for maintainability and future expansion.

---

## Features

### Moderation and Server Utilities

The bot provides a comprehensive set of tools for server administrators and moderators.

* Ban
* Kick
* Mute
* Warn
* Warning management
* Purge
* Channel locking
* Jail system
* AFK system
* Ticket system
* User information
* Server information
* Permission-aware moderation
* Automated moderation logging

### Advanced Logging

Server activity can be organized into 8 dedicated logging categories, providing moderators with better visibility into important events.

Logging can cover areas such as:

* Member activity
* Moderation actions
* Message events
* Voice activity
* Server changes
* Role changes
* Channel changes
* Administrative events

---

## Music System

The music module is powered by Lavalink 4.2.2 with Wavelink 3.4.1.

### Interactive Music Controls

The bot provides an interactive control panel for managing playback without relying exclusively on commands.

Features include:

* Play / Resume
* Pause
* Skip
* Stop
* Volume control
* Loop modes
* Autoplay
* Queue management
* Voice disconnect
* 24/7 playback mode

### Playback Architecture

Audio processing is handled through Lavalink, providing a dedicated audio backend while keeping the Discord bot responsive.

The system is designed around:

* Low-latency playback
* Queue-based music management
* Lavalink node connectivity
* Persistent player state
* Playback recovery
* Interactive controls

---

## Technical Problem Solving

One of the more challenging parts of this project was maintaining compatibility between the selected versions of Wavelink and Lavalink.

### Custom Wavelink Compatibility Patch

During development, a compatibility issue caused the required `channelId` field to be missing from the data exchanged between the libraries.

Instead of replacing the entire audio stack, the project implements a custom patch to restore the required field and maintain compatibility between:

```text
Wavelink 3.4.1
        |
Custom Compatibility Patch
        |
Lavalink 4.2.2
        |
Discord Voice
```

This allowed the music system to maintain stable end-to-end audio connectivity while working with the selected dependency versions.

> The patch is specific to the compatibility issue encountered during development. If dependency versions are changed, the patch should be reviewed accordingly.

---

## YouTube OAuth

The Lavalink YouTube plugin is configured with OAuth authentication to help address playback restrictions encountered during development.

This configuration is handled on the Lavalink side rather than exposing authentication credentials through the Discord bot itself.

**Never commit OAuth credentials, tokens, or other secrets to the repository.**

---

## Architecture

The project follows a modular structure to keep commands and systems separated.

```text
Incredibles/
|
├── cogs/
│   ├── moderation/
│   ├── music/
│   ├── utility/
│   ├── tickets/
│   └── ...
|
├── database/
|
├── logs/
|
├── .env
├── main.py
├── requirements.txt
└── README.md
```

The exact directory structure may vary depending on the current repository implementation.

The modular approach makes it easier to:

* Add new commands
* Maintain individual systems
* Debug features
* Update dependencies
* Expand the bot without heavily modifying the core application

---

## Tech Stack

| Component            | Technology                     |
| -------------------- | ------------------------------ |
| Language             | Python                         |
| Discord Framework    | Nextcord                       |
| Audio Backend        | Lavalink 4.2.2                 |
| Lavalink Wrapper     | Wavelink 3.4.1                 |
| Database / Storage   | SQLite / JSON                  |
| Configuration        | Environment Variables / `.env` |
| Music Authentication | YouTube OAuth                  |

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/00AbdullahZahid/Incredibles.git
cd Incredibles
```

## 2. Install Dependencies

Create a virtual environment if desired:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

---

## 3. Configure Lavalink

Download and configure Lavalink 4.2.2.

Your Lavalink installation should contain the required configuration files, including:

```text
Lavalink/
├── Lavalink.jar
└── application.yml
```

Configure the Lavalink node according to your environment.

If YouTube OAuth is required, configure the appropriate OAuth credentials in the Lavalink YouTube plugin configuration.

---

## 4. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
BOT_TOKEN=your_discord_bot_token

LAVALINK_HOST=127.0.0.1
LAVALINK_PORT=2333
LAVALINK_PASSWORD=your_lavalink_password
```

> **Important:** Never commit your `.env` file or any secret credentials to GitHub.

Add it to `.gitignore`:

```gitignore
.env
__pycache__/
*.pyc
logs/
```

---

## 5. Start Lavalink

Start the Lavalink server first:

```bash
java -jar Lavalink.jar
```

Make sure the Lavalink node is running and accessible using the host, port, and password configured in the bot.

---

## 6. Start the Bot

Once Lavalink is running:

```bash
python main.py
```

The bot should connect to Discord and establish a connection with the Lavalink node.

---

# Configuration

Before starting the bot, make sure you have:

* A Discord Bot Token
* Required Discord intents enabled
* A running Lavalink 4.2.2 server
* Correct Lavalink credentials
* Correct YouTube OAuth configuration if required
* Required environment variables configured

---

# Security

This project uses environment-based configuration for sensitive information.

Do not commit:

```text
BOT_TOKEN
LAVALINK_PASSWORD
YouTube OAuth credentials
API keys
Private configuration files
```

If a secret is accidentally exposed, revoke and regenerate it immediately.

---

# Compatibility

The project was developed and tested around the following versions:

```text
Python
Nextcord
Wavelink 3.4.1
Lavalink 4.2.2
```

Because the project contains a custom compatibility patch, upgrading Wavelink or Lavalink may require changes to the patch implementation.

---

# Project Goals

The primary goals of Incredibles are:

* Build a reliable multi-purpose Discord bot
* Provide powerful server-management tools
* Create a seamless music experience
* Maintain a modular and maintainable codebase
* Solve real-world compatibility problems between third-party libraries
* Demonstrate practical backend development and API integration skills

---

# Developer Note

Incredibles was built as a practical demonstration of backend development, third-party API integration, debugging, and software maintenance.

One of the key technical challenges was integrating different versions of the Discord, Wavelink, Lavalink, and YouTube ecosystem while maintaining stable audio connectivity.

Rather than simply replacing a dependency when compatibility issues appeared, the project involved investigating the underlying data flow and implementing a targeted library-level compatibility patch.

This project demonstrates practical experience in debugging, dependency management, integration engineering, and backend problem-solving.

---

# License

Add your preferred license here.

For example:

```text
MIT License
```

---

# Support

If you find the project useful or interesting, consider giving the repository a star on GitHub.

Built with Python and Nextcord.
