import os
import logging

try:
    from pydotenv import load_dotenv as _load_dotenv  # type: ignore
except ImportError:  # pragma: no cover - fallback when pydotenv 未安装
    from dotenv import load_dotenv as _load_dotenv  # type: ignore

from voyager import Voyager
from voyager.agents import skill
from voyager.utils import configure_root_logger, silence_noisy_loggers, get_logger


_load_dotenv()

# Configure logging first thing
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
configure_root_logger(log_dir="logs", level=log_level)
silence_noisy_loggers()

logger = get_logger(__name__)

def _require_env(name: str) -> str:
    """Ensure that required environment variables are set."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}. Configure it in your .env file.")
    return value


azure_login = {
    "client_id": _require_env("AZURE_CLIENT_ID"),
    "redirect_url": os.getenv("AZURE_REDIRECT_URL", "https://127.0.0.1/auth-response"),
    "secret_value": _require_env("AZURE_SECRET_VALUE"),
    "version": os.getenv("MINECRAFT_VERSION", "fabric-loader-0.16.14-1.19"),
}

openai_api_key = _require_env("OPENAI_API_KEY")
dashscope_api_key = _require_env("DASHSCOPE_API_KEY")

dashscope_base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

logger.info("Starting Voyager application")
logger.info(f"Minecraft version: {azure_login['version']}")

try:
    voyager = Voyager(
        azure_login=azure_login,
        openai_api_key=openai_api_key,
        dashscope_api_key=dashscope_api_key,
        dashscope_base_url=dashscope_base_url,
        action_agent_model_name="qwen-plus",
        curriculum_agent_model_name="qwen-plus",
        critic_agent_model_name="qwen-plus",
        skill_manager_model_name="qwen-plus"
    )
    logger.info("Voyager instance created successfully")
except Exception as e:
    logger.error(f"Failed to initialize Voyager: {e}", exc_info=True)
    exit(1)

voyager.learn()