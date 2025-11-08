import os
import subprocess
import argparse

try:
    from pydotenv import load_dotenv as _load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    from dotenv import load_dotenv as _load_dotenv  # type: ignore

import minecraft_launcher_lib as mcl
import tqdm
from minecraft_launcher_lib.types import CallbackDict
from loguru import logger


_load_dotenv()


def _require_env(name: str) -> str:
    """Fetch required environment variables, raising if missing."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required. Configure it in your .env file before running.")
    return value

logger.add("minecraft_launcher.log", rotation="1 MB")

directory = mcl.utils.get_minecraft_directory()

azure_login = {
    "client_id": _require_env("AZURE_CLIENT_ID"),
    "redirect_uri": os.getenv("AZURE_REDIRECT_URL", "https://127.0.0.1/auth-response"),
    "secret_value": _require_env("AZURE_SECRET_VALUE"),
    "version": os.getenv("MINECRAFT_LAUNCHER_VERSION", os.getenv("MINECRAFT_VERSION", "fabric-loader-0.17.3-1.19")),
}

def install_minecraft_version(version):
    """
    Install a specific version of Minecraft using minecraft_launcher_lib.
    
    :param version: The version of Minecraft to install (e.g., '1.16.5').
    """
    progress_bar = tqdm.tqdm(total=100, desc=f"Installing Minecraft {version}", unit='%', leave=True)
    def set_install_status(status: str) -> None:
        """
        Callback function to update the installation status.
        
        :param status: The current status of the installation.
        """
        progress_bar.set_description(f"Installing Minecraft {version}: {status}")
    def set_install_progress(progress: int) -> None:
        """
        Callback function to update the installation progress.
        
        :param progress: The current progress of the installation.
        """
        progress_bar.update(progress - progress_bar.n)
    def set_max(max_value: int) -> None:
        """
        Callback function to set the maximum value for the progress bar.
        
        :param max_value: The maximum value for the progress bar.
        """
        progress_bar.total = max_value
        progress_bar.refresh()
    try:
        print(f"Installing Minecraft version {version}...")
        callbacks: CallbackDict = {
            "setProgress": set_install_progress,
            "setStatus": set_install_status,
            "setMax": set_max,
        }
        mcl.install.install_minecraft_version(version, minecraft_directory=directory, callback=callbacks)
        logger.info(f"Successfully installed Minecraft version {version}.")
    except Exception as e:
        logger.error(f"An error occurred while installing Minecraft version {version}: {e}")

def launch_minecraft_version(version, test: bool = True):
    """
    Launch a specific version of Minecraft using minecraft_launcher_lib.
    
    :param version: The version of Minecraft to launch (e.g., '1.16.5').
    """
    if test:
        logger.info(f"Testing launch for Minecraft version {version}...")
        # Here you can add any test logic if needed
        user_options = mcl.utils.generate_test_options()
    else:
        raise NotImplementedError("Play mode is not implemented in this example.")
    
    try:
        mc_commands = mcl.command.get_minecraft_command(
            version=version,
            minecraft_directory=directory,
            options=user_options
        )
        mc = subprocess.run(mc_commands, capture_output=True)
        logger.info(f"Successfully launched Minecraft version {version}.")
        return mc
    except Exception as e:
        logger.error(f"An error occurred while launching Minecraft version {version}: {e}")

def main(version):
    version = version  # Example version to install and launch
    logger.info(f"Minecraft Directory: {directory}")
    logger.info(f"Installing Minecraft version: {version}")
    install_minecraft_version(version)
    complete = launch_minecraft_version(version)
    if complete.returncode == 0:
        logger.info("Minecraft launched successfully.")
    else:
        logger.error(f"Error launching Minecraft: {complete.stderr.decode()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minecraft Launcher Script")
    parser.add_argument('--version', type=str, default='fabric-loader-0.16.14-1.19', help='Minecraft version to install and launch')
    args = parser.parse_args()
    version = args.version
    main(version)