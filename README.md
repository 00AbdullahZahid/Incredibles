Discord Moderation & Music Bot
A comprehensive, high-performance Discord utility bot built with Python. This project combines advanced server management tools with a robust, professional-grade music streaming system.

🚀 Key Features
Advanced Moderation & Utility
Full Moderation Suite: Includes ban, kick, mute, warn, purge, and lock commands.

Automated Systems: AFK status tracking and a specialized Ticket System for user support.

Deep Logging: Automatic activity tracking across 8 separate log categories for maximum server transparency.

Visuals: Information delivered via clean, color-coded embeds for a professional UI/UX.

Pro-Grade Music System
Technical Engineering: Successfully bridged Wavelink 3.4.1 to Lavalink 4.2.2 by custom-patching the channelId field dependency.

YouTube Integration: Configured with OAuth authentication to ensure stable playback and bypass common streaming restrictions.

Interactive Controls: Full music controller with queue management, looping, autoplay, and volume normalization.

Rich Audio: Powered by Lavalink for low-latency, high-quality sound.

🛠️ Technical Stack
Language: Python

Library: Discord.py / Nextcord (Adjust based on what you used)

Audio Provider: Lavalink 4.2.2

Wrapper: Wavelink 3.4.1 (Patched)

Database: SQLite / MySQL (Add yours here)

🔧 Installation & Setup
Clone the repository:

Bash
git clone https://github.com/00AbdullahZahid/your-repo-name.git
Install dependencies:

Bash
pip install -r requirements.txt
Configure Lavalink:
Ensure you have a Lavalink.jar running with the version 4.2.2.

Environment Variables:
Create a .env file and add your BOT_TOKEN and Lavalink credentials.

Run the bot:

Bash
python main.py
🛡️ Permission System
The bot features a hierarchical permission check system, ensuring that only authorized staff can access sensitive moderation commands, while logging all actions to the designated administrative channels.
