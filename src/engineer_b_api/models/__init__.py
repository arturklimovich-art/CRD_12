# -*- coding: utf-8 -*-
"""
Models package для Engineer B API
Exports: Roadmap models, Truth models
"""

# Roadmap Models
from .roadmap import (
    # Enums
    BlockStatus,
    BlockKind,
    TaskStatus,
    TaskKind,
    EventType,
    
    # Block models
    RoadmapBlockBase,
    RoadmapBlockCreate,
    RoadmapBlockUpdate,
    RoadmapBlock,
    
    # Task models
    RoadmapTaskBase,
    RoadmapTaskCreate,
    RoadmapTaskUpdate,
    RoadmapTask,
    
    # Event models
    RoadmapEventCreate,
    RoadmapEvent,
    
    # Dashboard models
    DashboardBlock,
    RoadmapDashboard,
    
    # Query/Response models
    RoadmapQuery,
    RoadmapResponse,
    RoadmapSyncResponse,
)

# Truth Models
from .truth import (
    # Enums
    VerdictStatus,
    EvidenceKind,
    
    # TruthRevision models
    TruthRevisionBase,
    TruthRevisionCreate,
    TruthRevision,
    
    # EvidenceArtifact models
    EvidenceArtifactBase,
    EvidenceArtifactCreate,
    EvidenceArtifact,
    
    # TaskVerdict models
    TaskVerdictBase,
    TaskVerdictCreate,
    TaskVerdictUpdate,
    TaskVerdict,
    
    # TruthMatrix models
    TruthMatrixRow,
    TruthMatrix,
    
    # Dashboard models
    TruthDashboard,
    
    # Verification models
    VerifyTaskRequest,
    VerifyTaskResponse,
    
    # Query/Response models
    TruthQuery,
    TruthResponse,
)

__all__ = [
    # Roadmap Enums
    "BlockStatus",
    "BlockKind",
    "TaskStatus",
    "TaskKind",
    "EventType",
    
    # Roadmap Models
    "RoadmapBlockBase",
    "RoadmapBlockCreate",
    "RoadmapBlockUpdate",
    "RoadmapBlock",
    "RoadmapTaskBase",
    "RoadmapTaskCreate",
    "RoadmapTaskUpdate",
    "RoadmapTask",
    "RoadmapEventCreate",
    "RoadmapEvent",
    "DashboardBlock",
    "RoadmapDashboard",
    "RoadmapQuery",
    "RoadmapResponse",
    "RoadmapSyncResponse",
    
    # Truth Enums
    "VerdictStatus",
    "EvidenceKind",
    
    # Truth Models
    "TruthRevisionBase",
    "TruthRevisionCreate",
    "TruthRevision",
    "EvidenceArtifactBase",
    "EvidenceArtifactCreate",
    "EvidenceArtifact",
    "TaskVerdictBase",
    "TaskVerdictCreate",
    "TaskVerdictUpdate",
    "TaskVerdict",
    "TruthMatrixRow",
    "TruthMatrix",
    "TruthDashboard",
    "VerifyTaskRequest",
    "VerifyTaskResponse",
    "TruthQuery",
    "TruthResponse",
]
