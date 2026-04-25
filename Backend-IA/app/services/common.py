"""
Schémas communs partagés entre tous les modules.
"""
from enum import Enum


class DocumentType(str, Enum):
    PDF  = "pdf"
    DOCX = "docx"
    PPTX = "pptx"


class IngestStatus(str, Enum):
    OK     = "ok"
    EMPTY  = "empty"
    FAILED = "failed"
    ERROR = "error"