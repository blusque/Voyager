import os
import re
from typing import Any

import voyager.utils as U
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qwq import ChatQwen

from voyager.prompts import load_prompt
from voyager.control_primitives import load_control_primitives
from voyager.utils.telemetry import ensure_posthog_compat

ensure_posthog_compat()

logger = U.get_logger(__name__)

class SkillManager:
    def __init__(
        self,
        model_name="qwen-plus",
        temperature=0,
        retrieval_top_k=5,
        request_timout=120,
        ckpt_dir="ckpt",
        resume=False,
    ):
        logger.info(f"Initializing SkillManager (model={model_name}, top_k={retrieval_top_k}, resume={resume})")
        if re.search(r"^qwen-", model_name):
            logger.info(
                f"\033[32mUsing Qwen model {model_name} for Action Agent\033[0m"
            )
            self.llm = ChatQwen(
                model_name=model_name,
                temperature=temperature,
                request_timeout=request_timout,
            )
        elif re.search(r"^gpt-", model_name):
            logger.info(
                f"\033[32mUsing GPT model {model_name} for Action Agent\033[0m"
            )
            self.llm = ChatOpenAI(
                model_name=model_name,
                temperature=temperature,
                request_timeout=request_timout,
            )
        else:
            raise ValueError(
                f"Unsupported model name {model_name} for Action Agent. "
                "Please use a QwQ or GPT model."
            )
        U.f_mkdir(f"{ckpt_dir}/skill/code")
        U.f_mkdir(f"{ckpt_dir}/skill/description")
        U.f_mkdir(f"{ckpt_dir}/skill/vectordb")
        # programs for env execution
        self.control_primitives = load_control_primitives()
        if resume:
            logger.info(f"\033[33mLoading Skill Manager from {ckpt_dir}/skill\033[0m")
            self.skills = U.load_json(f"{ckpt_dir}/skill/skills.json")
        else:
            self.skills = {}
        self.retrieval_top_k = retrieval_top_k
        self.ckpt_dir = ckpt_dir
        self.vectordb = Chroma(
            collection_name="skill_vectordb",
            embedding_function=OpenAIEmbeddings(),
            persist_directory=f"{ckpt_dir}/skill/vectordb",
        )
        assert self.vectordb._collection.count() == len(self.skills), (
            f"Skill Manager's vectordb is not synced with skills.json.\n"
            f"There are {self.vectordb._collection.count()} skills in vectordb but {len(self.skills)} skills in skills.json.\n"
            f"Did you set resume=False when initializing the manager?\n"
            f"You may need to manually delete the vectordb directory for running from scratch."
        )

    @property
    def programs(self):
        programs = ""
        for skill_name, entry in self.skills.items():
            programs += f"{entry['code']}\n\n"
        for primitives in self.control_primitives:
            programs += f"{primitives}\n\n"
        return programs

    def add_new_skill(self, info):
        if info["task"].startswith("Deposit useless items into the chest at"):
            # No need to reuse the deposit skill
            return
        program_name = info["program_name"]
        program_code = info["program_code"]
        skill_description = self.generate_skill_description(program_name, program_code)
        logger.info(
            f"\033[33mSkill Manager generated description for {program_name}:\n{skill_description}\033[0m"
        )
        if program_name in self.skills:
            logger.info(f"\033[33mSkill {program_name} already exists. Rewriting!\033[0m")
            self.vectordb._collection.delete(ids=[program_name])
            i = 2
            while f"{program_name}V{i}.js" in os.listdir(f"{self.ckpt_dir}/skill/code"):
                i += 1
            dumped_program_name = f"{program_name}V{i}"
        else:
            dumped_program_name = program_name
        self.vectordb.add_texts(
            texts=[skill_description],
            ids=[program_name],
            metadatas=[{"name": program_name}],
        )
        self.skills[program_name] = {
            "code": program_code,
            "description": skill_description,
        }
        assert self.vectordb._collection.count() == len(
            self.skills
        ), "vectordb is not synced with skills.json"
        U.dump_text(
            program_code, f"{self.ckpt_dir}/skill/code/{dumped_program_name}.js"
        )
        U.dump_text(
            skill_description,
            f"{self.ckpt_dir}/skill/description/{dumped_program_name}.txt",
        )
        U.dump_json(self.skills, f"{self.ckpt_dir}/skill/skills.json")
        self.vectordb.persist()

    def generate_skill_description(self, program_name, program_code):
        messages = [
            SystemMessage(content=load_prompt("skill")),
            HumanMessage(
                content=program_code
                + "\n\n"
                + f"The main function is `{program_name}`."
            ),
        ]
        response = self.llm(messages)
        description_text = self._message_content_to_text(response.content)
        skill_description = f"    // {description_text}"
        return f"async function {program_name}(bot) {{\n{skill_description}\n}}"

    def retrieve_skills(self, query):
        k = min(self.vectordb._collection.count(), self.retrieval_top_k)
        if k == 0:
            logger.debug("No skills available in vectordb")
            return []
        logger.debug(f"Retrieving top {k} skills for query")
        logger.info(f"\033[33mSkill Manager retrieving for {k} skills\033[0m")
        docs_and_scores = self.vectordb.similarity_search_with_score(query, k=k)
        skill_names = [doc.metadata['name'] for doc, _ in docs_and_scores]
        logger.info(f"Retrieved skills: {', '.join(skill_names)}")
        logger.info(
            f"\033[33mSkill Manager retrieved skills: "
            f"{', '.join(skill_names)}\033[0m"
        )
        skills = []
        for doc, _ in docs_and_scores:
            skills.append(self.skills[doc.metadata["name"]]["code"])
        return skills

    def _message_content_to_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict):
                    text = block.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "\n".join(parts)
        return str(content)
    
    def test_yourself(self):
        try:
            logger.info("Skill Manager test_yourself called")
            response = self.llm(
                [
                    SystemMessage(content=load_prompt("skill_test")),
                    HumanMessage(content="Test yourself."),
                ]
            )
        except Exception as e:
            logger.error(f"Skill Manager test_yourself error: {e}")
            return False
        logger.info(f"Skill Manager test_yourself response: {response}")
        return True
