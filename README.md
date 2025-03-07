# RemoteBot
A Telegram bot that allows users to execute commands on a remote PC.

## Features
- Execute shell commands remotely.
- Take and send screenshots.
- Start and stop screen recording with automatic video sending.
- User authentication via Telegram username.

## Installation
1. Clone this repository:
   ```
   git clone https://github.com/JamesCoalchi/RemoteBot.git
   cd telegram-remote-bot
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run setup.py and configure your .env file
   ```
   python setup.py
   ```
4. Run the bot:
   ```python
   python main.py
   ```

## Commands
| Command          | Description |
|-----------------|-------------|
| `/start`        | Show available commands. |
| `/cmd [command]` | Execute a shell command. |
| `/screenshot`   | Take and send a screenshot. |
| `/record_start` | Start screen recording. |
| `/record_stop`  | Stop recording and send the video. |

## Notes
- The bot only allows authorized users to send commands.
- Recordings are limited to the duration set in `MAX_RECORD_SECONDS`.
- Recording FPS is limited to the duration set in `RECORD_FPS`.
