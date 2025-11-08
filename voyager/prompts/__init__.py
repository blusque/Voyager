from typing import cast

import pkg_resources
import voyager.utils as U


def load_prompt(prompt: str) -> str:
    package_path = pkg_resources.resource_filename("voyager", "")
    return cast(str, U.load_text(f"{package_path}/prompts/{prompt}.txt"))
