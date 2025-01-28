from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.config import settings
import torch
import logging

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self, vector_store):
        self.device = settings.device
        self.model, self.tokenizer = self._load_model()
        self.vector_store = vector_store
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        self.prompt = hub.pull("rlm/rag-prompt")
        self.setup_chain()

    def _load_model(self):
        model = AutoModelForCausalLM.from_pretrained(
            settings.model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto"
        )
        tokenizer = AutoTokenizer.from_pretrained(settings.model_name)
        return model, tokenizer

    def setup_chain(self):
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        self.rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self._generate_answer
        )

    async def get_answer(self, question: str):
        try:
            answer = await self.rag_chain.ainvoke(question)
            sources = await self._get_sources(question)
            return {
                "answer": answer,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Retrieval error: {str(e)}")
            raise

    async def _generate_answer(self, prompt: str):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            inputs.input_ids,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    async def _get_sources(self, question: str):
        docs = await self.retriever.ainvoke(question)
        return list(set(doc.metadata.get("source", "") for doc in docs))