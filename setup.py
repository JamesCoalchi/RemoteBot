# Will create / edit a .env file with user input

def save_env():
    def get_input(value_name, default_value=None, is_int=False, help=False):
        while True:
            if help:
                print(f"Help: Input a list of users who can access the bot. Use ; between usernames to add more than one user.")

            if default_value is not None:
                user_input = input(f"Enter {value_name} (or 'd' to set it to default (default: {default_value})): ").strip()
                if user_input.lower() == 'd':
                    return default_value
            else:
                user_input = input(f"Enter {value_name}:\n>>> ").strip()

            if is_int:
                try:
                    user_input = int(user_input)
                except ValueError:
                    print(f"Invalid input. {value_name} must be an integer.")
                    continue

            if input(f"Is '{user_input}' correct? (y/n):\n>>> ").lower() == 'y':
                print(f"{value_name} saved.")
                return user_input.replace("@", "")
            else:
                print(f"Please re-enter the correct {value_name}.")

    BOT_TOKEN = get_input("BOT_TOKEN", None)
    AUTHORIZED_USERS = get_input("AUTHORIZED_USERS", None, help=True)
    RECORD_FPS = get_input("RECORD_FPS", 10, is_int=True)
    MAX_RECORD_SECONDS = get_input("MAX_RECORD_SECONDS", 120, is_int=True)

    env_content = f'BOT_TOKEN="{BOT_TOKEN}" # Input your bot token from @BotFather\nAUTHORIZED_USERS="{AUTHORIZED_USERS}" # Input a list of users who can access the bot. Use ; between usernames to add more than one user.\nRECORD_FPS={RECORD_FPS} # High values will increase the file size and might result in an error.\nMAX_RECORD_SECONDS={MAX_RECORD_SECONDS} # High values will increase the file size and might result in an error.'

    with open('.env', 'w') as env:
        env.write(env_content)

    print(".env file has been successfully created/updated.")

if __name__ == "__main__":
    save_env()