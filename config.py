import os

# Bot configuration
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "your_bot_token_here")
COMMAND_PREFIX = "!"

# AI API configuration
PAWAN_API_KEY = os.getenv("PAWAN_API_KEY", "your_pawan_api_key_here")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_key_here")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_key_here")

# Fact-checking sources
FACT_CHECK_SOURCES = {
    "snopes": "https://www.snopes.com/",
    "factcheck": "https://www.factcheck.org/",
    "politifact": "https://www.politifact.com/",
    "reuters_fact_check": "https://www.reuters.com/fact-check/",
    "ap_fact_check": "https://apnews.com/hub/ap-fact-check"
}

# Bot settings
MAX_COMMANDS_PER_MINUTE = 5
MAX_MESSAGE_LENGTH = 2000
CONFIDENCE_THRESHOLD = 0.7

# Automatic misinformation detection settings
AUTO_DETECT_ENABLED = True
AUTO_DETECT_TRUTHINESS_THRESHOLD = 50  # Reply if truthiness is below this percentage
AUTO_DETECT_CONFIDENCE_THRESHOLD = 0.6  # Only reply if AI confidence is above this
AUTO_DETECT_MIN_MESSAGE_LENGTH = 20  # Minimum message length to check
AUTO_DETECT_RATE_LIMIT = 2  # Maximum auto-checks per user per 5 minutes

# Colors for embeds
COLORS = {
    "success": 0x27ae60,
    "warning": 0xf39c12,
    "error": 0xe74c3c,
    "info": 0x3498db,
    "neutral": 0x95a5a6
}
