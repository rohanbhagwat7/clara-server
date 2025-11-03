"""
Pattern Learning Package

Learns from technician behavior patterns and provides proactive suggestions.
"""

from .pattern_learner import (
    PatternLearner,
    ActionSequence,
    PatternSuggestion,
    get_pattern_learner,
)

__all__ = [
    'PatternLearner',
    'ActionSequence',
    'PatternSuggestion',
    'get_pattern_learner',
]
