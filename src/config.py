"""
Scout-Edge configuration module.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Tool-specific settings (with defaults)
ARXIV_MAX_RESULTS = int(os.getenv("ARXIV_MAX_RESULTS", "10"))
GITHUB_MAX_RESULTS = int(os.getenv("GITHUB_MAX_RESULTS", "10"))

# LLM settings
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# Database settings
VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH", "./data/vectorstore")

# Application settings
VERBOSE_MODE = os.getenv("VERBOSE_MODE", "False").lower() == "true"
DATA_DIR = os.getenv("DATA_DIR", "./data")

# ArXiv categories
ARXIV_CATEGORIES = [
    "cs.AI",  # Artificial Intelligence
    "cs.CL",  # Computational Linguistics
    "cs.CV",  # Computer Vision
    "cs.LG",  # Machine Learning
    "cs.NE",  # Neural and Evolutionary Computing
    "stat.ML",  # Statistical Machine Learning
]

# HuggingFace categories
HUGGINGFACE_MODEL_TYPES = [
    "text-generation",
    "text-classification",
    "token-classification",
    "question-answering",
    "summarization",
    "translation",
    "conversational",
    "image-classification",
    "object-detection",
    "image-segmentation",
    "text-to-image",
    "image-to-text",
    "audio-classification",
    "automatic-speech-recognition",
    "text-to-speech",
]

# GitHub tags
GITHUB_TAGS = [
    "artificial-intelligence",
    "machine-learning",
    "deep-learning",
    "nlp",
    "computer-vision",
    "neural-network",
    "llm",
    "transformer",
    "generative-ai",
    "diffusion-model",
]

# Application settings
APP_NAME = "Scout-Edge"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "A toolkit for tracking current trends and developments in AI"
