"""
AI features analysis and scoring.
"""
import re
from typing import Dict, Any, List, Optional


class AIAnalyzer:
    """Analyze content for AI-related features and compute scores."""

    # Keywords and patterns for AI detection
    AI_KEYWORDS = {
        "high": [
            "machine learning", "deep learning", "neural network", "transformer",
            "artificial intelligence", "natural language processing", "nlp",
            "computer vision", "reinforcement learning", "generative ai",
            "large language model", "llm", "gpt", "bert", "diffusion model",
            "pytorch", "tensorflow", "hugging face", "langchain"
        ],
        "medium": [
            "model training", "inference", "embedding", "tokenizer", "fine-tuning",
            "prompt engineering", "vector database", "semantic search",
            "classification", "regression", "clustering", "api endpoint"
        ],
        "low": [
            "ai", "ml", "data science", "prediction", "automation",
            "intelligent", "smart", "cognitive", "learning algorithm"
        ]
    }

    FRAMEWORK_PATTERNS = [
        r"pytorch", r"tensorflow", r"keras", r"jax", r"scikit-learn",
        r"huggingface", r"transformers", r"langchain", r"llama",
        r"fastai", r"mxnet", r"caffe", r"onnx"
    ]

    MODEL_PATTERNS = [
        r"gpt-\d+", r"bert", r"t5", r"llama-?\d*", r"mistral",
        r"claude", r"gemini", r"stable diffusion", r"dall-?e",
        r"whisper", r"clip", r"resnet", r"vit", r"yolo"
    ]

    def analyze(self, text: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze text for AI features and compute score.

        Returns:
            Dict with 'score', 'facets', and 'signals' keys
        """
        text_lower = text.lower()
        title_lower = title.lower() if title else ""
        combined = f"{title_lower} {text_lower}"

        facets = {}
        signals = []

        # Keyword scoring
        keyword_score = 0
        keyword_matches = []

        for weight, keywords in [("high", self.AI_KEYWORDS["high"]),
                                  ("medium", self.AI_KEYWORDS["medium"]),
                                  ("low", self.AI_KEYWORDS["low"])]:
            for keyword in keywords:
                count = combined.count(keyword)
                if count > 0:
                    keyword_matches.append({"keyword": keyword, "count": count, "weight": weight})

                    if weight == "high":
                        keyword_score += count * 3
                    elif weight == "medium":
                        keyword_score += count * 2
                    else:
                        keyword_score += count * 1

        facets["keyword_matches"] = keyword_matches[:20]  # Top 20
        facets["keyword_score"] = min(keyword_score, 50)  # Cap at 50

        # Framework detection
        frameworks = []
        for pattern in self.FRAMEWORK_PATTERNS:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            if matches:
                frameworks.extend(set(matches))

        facets["frameworks"] = list(set(frameworks))[:10]
        framework_score = min(len(facets["frameworks"]) * 5, 25)

        # Model detection
        models = []
        for pattern in self.MODEL_PATTERNS:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            if matches:
                models.extend(set(matches))

        facets["models"] = list(set(models))[:10]
        model_score = min(len(facets["models"]) * 4, 20)

        # GitHub/code indicators
        code_score = 0
        if "github.com" in combined:
            code_score += 5
            signals.append("github_repo")
        if re.search(r"```|`[^`]+`", text):
            code_score += 3
            signals.append("code_snippets")
        if re.search(r"\binstall\b|\bpip\b|\bnpm\b", combined):
            code_score += 2
            signals.append("installation_instructions")

        facets["code_indicators"] = code_score

        # Research indicators
        research_score = 0
        if "arxiv.org" in combined:
            research_score += 10
            signals.append("arxiv_paper")
        if re.search(r"\babstract\b.*?\bmethod", combined):
            research_score += 5
            signals.append("research_structure")

        facets["research_indicators"] = research_score

        # Compute final score (0-100)
        raw_score = (
            facets["keyword_score"] +
            framework_score +
            model_score +
            code_score +
            research_score
        )

        # Normalize to 0-100
        final_score = min(raw_score, 100)

        # Boost score if title has strong AI keywords
        if title:
            title_keywords = sum(1 for kw in self.AI_KEYWORDS["high"] if kw in title_lower)
            if title_keywords > 0:
                final_score = min(final_score * 1.2, 100)

        facets["signals"] = signals

        return {
            "score": round(final_score, 2),
            "facets": facets
        }