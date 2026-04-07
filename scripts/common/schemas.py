from typing import List, Optional

from pydantic import BaseModel, Field


class ExtractResult(BaseModel):
    raw_text: str = ""
    visible_code: str = ""
    task_relevant_text: str = ""
    task_relevant_code: str = ""
    irrelevant_ui_text: List[str] = Field(default_factory=list)
    ui_hints: List[str] = Field(default_factory=list)
    language_guess: Optional[str] = None
    confidence: float = 0.0
    missing_or_cut_off_parts: List[str] = Field(default_factory=list)
    code_appears_complete: bool = False
    task_text_appears_complete: bool = False


class ClassifyResult(BaseModel):
    task_type: str = "unknown"
    programming_language: Optional[str] = None
    requires_execution: bool = False
    requires_reasoning: bool = False
    task_relevant_content_complete: bool = True
    non_task_ui_is_cut_off: bool = False
    is_condition_complete: bool = True
    confidence: float = 0.0


class QASolverResult(BaseModel):
    final_answer: str = ""
    answer_type: str = "text"
    confidence: float = 0.0
    notes: str = ""


class CodeReconstructionResult(BaseModel):
    language: Optional[str] = None
    code: str = ""
    task_intent: str = ""
    confidence: float = 0.0


class CodeExecutionResult(BaseModel):
    status: str = "error"
    stdout: str = ""
    stderr: str = ""
    returncode: int = 1


class FinalAnswer(BaseModel):
    answer: str = ""
    answer_kind: str = "text"
    confidence: float = 0.0
    source: str = "unknown"