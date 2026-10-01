"""StructuralPro local/offline AI facade.

The AI layer is deliberately provider-independent. It can use a local GGUF
model through llama-cpp-python when that optional runtime is installed, while
the deterministic QA engine remains available without any model or network.
"""

from dataclasses import dataclass
from pathlib import Path
import re

try:
    from llama_cpp import Llama
except Exception:  # optional local runtime
    Llama = None


@dataclass
class AIResponse:
    text: str
    source: str = "local-rule-engine"
    confidence: float = 1.0


class LocalAIEngine:
    def __init__(self, model_dir=None, model_path=None, n_ctx=4096):
        self.model_dir = Path(model_dir or Path(__file__).resolve().parents[2] / "models")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = Path(model_path) if model_path else self._find_model()
        self.n_ctx = n_ctx
        self._llm = None
        self._load_error = None
        self._try_load_local_model()

    def _find_model(self):
        models = sorted(self.model_dir.glob("*.gguf"))
        return models[0] if models else None

    def _try_load_local_model(self):
        if not self.model_path or Llama is None:
            return
        try:
            self._llm = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                verbose=False,
            )
        except Exception as exc:
            self._load_error = str(exc)
            self._llm = None

    @property
    def is_local(self):
        return True

    @property
    def has_llm_model(self):
        return self.model_path is not None and self._llm is not None

    @property
    def runtime_available(self):
        return Llama is not None

    def inspect_project(self, project):
        project = project if isinstance(project, dict) else {}
        missing = []
        takeoffs = project.get("takeoffs", []) or []
        if not project.get("name"):
            missing.append("نام پروژه")
        if not takeoffs:
            missing.append("حداقل یک متره")
        for i, item in enumerate(takeoffs, 1):
            if not item.get("member_code"):
                missing.append(f"کد عضو متره {i}")
            if not item.get("quantities"):
                missing.append(f"خروجی متره عضو {i}")
        return AIResponse(
            self._format_check(missing, len(takeoffs)),
            confidence=0.99,
        )

    def answer(self, prompt, project=None):
        p = (prompt or "").strip()
        if project is not None and any(k in p for k in ("بررسی", "کنترل", "جا افتاده", "نقص", "متره")):
            return self.inspect_project(project)

        if self._llm is not None and p:
            return self._llm_answer(p, project)

        if re.search(r"آفلاین|اینترنت|آنلاین", p):
            return AIResponse(
                "StructuralPro در هسته و هوش مصنوعی به اینترنت وابسته نیست. "
                "اینترنت فقط برای همگام‌سازی، پشتیبان‌گیری و به‌روزرسانی اختیاری است."
            )

        return AIResponse(
            "پاسخ محلی آماده است. برای تحلیل عمیق‌تر، پروژه را در StructuralPro انتخاب کنید؛ "
            "اطلاعات پروژه برای پاسخ‌گویی محلی به سرویس خارجی ارسال نمی‌شود."
        )

    def _llm_answer(self, prompt, project=None):
        context = ""
        if project:
            context = f"Project summary: name={project.get('name', '')}, takeoffs={len(project.get('takeoffs', []) or [])}"
        system = (
            "You are StructuralPro Local AI, an offline construction quantity-takeoff assistant. "
            "Do not invent engineering values. If required inputs are missing, say so. "
            "Never claim that an AI answer replaces a deterministic engineering calculation."
        )
        user = f"{context}\nUser: {prompt}".strip()
        try:
            result = self._llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.1,
                max_tokens=700,
            )
            text = result["choices"][0]["message"]["content"].strip()
            return AIResponse(text, source="local-gguf", confidence=0.85)
        except Exception as exc:
            self._load_error = str(exc)
            return AIResponse(
                "مدل محلی در دسترس نبود؛ کنترل پایه آفلاین فعال است.",
                source="local-rule-engine",
                confidence=0.7,
            )

    def _format_check(self, missing, count):
        if not missing:
            return (
                f"کنترل اولیه پروژه انجام شد: {count} مورد متره موجود است و "
                "مورد ضروریِ شناخته‌شده‌ای ناقص نیست."
            )
        return "مواردی که باید بررسی شوند:\n" + "\n".join(f"• {item}" for item in missing)
