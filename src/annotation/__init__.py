"""Graph annotation package."""

from annotation.annotator import annotate_rim
from annotation.models import AnnotatedNode, AnnotationType

__all__ = [
    "AnnotatedNode",
    "AnnotationType",
    "annotate_rim",
]
