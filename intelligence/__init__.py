"""
Multi-Asset Intelligence System

A parallel scoring system for regulatory/fundamental-driven assets.
Complements Confluence V2 without modifying existing bot infrastructure.

Components:
- AssetClassifier: Routes assets to appropriate scorer
- RegulatoryScorer: Scores based on regulatory/institutional metrics
- MasterDecisionEngine: Unified interface for all scorers
"""

__version__ = "1.0.0"
__author__ = "CryptoIntel Hub"

from .asset_classifier import AssetClassifier
from .regulatory_scorer import RegulatoryScorer
from .master_decision import MasterDecisionEngine

__all__ = [
    'AssetClassifier',
    'RegulatoryScorer',
    'MasterDecisionEngine',
]
