🛡️ Incredibles - Advanced Discord Utility & Music Bot
A high-performance Discord bot engineered with Python and Nextcord, designed to provide professional-grade moderation and a seamless music streaming experience.

🌟 Key Highlights
Custom Library Patch: Solved compatibility issues between Wavelink 3.4.1 and Lavalink 4.2.2 by manually patching the missing channelId field, ensuring stable end-to-end audio connectivity.

Resilient Streaming: Integrated OAuth authentication within the YouTube plugin configuration to bypass playback restrictions and ensure consistent uptime.

Modular Architecture: Built using a clean, organized structure to handle complex command sets across moderation and entertainment.

🚀 Features
Professional Moderation & Utility
Comprehensive Suite: Robust commands for ban, kick, mute, warn, purge, and lock.

Automated Systems: Integrated AFK system and a custom Ticket System for server support management.

Advanced Logging: Automatic tracking across 8 distinct log categories, providing high visibility into server activity.

Information Retrieval: Detailed server and user info commands with color-coded embed responses.

Pro-Level Music Experience
Interactive UI: Full-featured music control panel with an intuitive interface.

Smart Playback: Supports queue management, looping, and autoplay functionality.

Precision Control: High-quality audio with volume normalization and low-latency streaming via Lavalink.

🛠️ Technical Stack
Language: Python

Framework: Nextcord

Audio Engine: Lavalink 4.2.2

Connection Wrapper: Wavelink 3.4.1 (Custom Patched)

Data Handling: JSON / SQLite (Edit based on your exact storage)

🔧 Installation & Configuration
Clone the Repo

Bash
git clone https://github.com/00AbdullahZahid/Incredibles.git
cd Incredibles
Install Dependencies

Bash
pip install -r requirements.txt
Lavalink Setup

Download Lavalink.jar (v4.2.2).

Ensure the application.yml is configured with the correct YouTube OAuth tokens.

Environment Variables

Create a .env file or update your config with your BOT_TOKEN and Lavalink node details.

Launch

Bash
python main.py
Developer Note
This project was built to demonstrate backend problem-solving, specifically in handling API integrations and third-party library maintenance.
