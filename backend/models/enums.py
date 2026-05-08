from enum import Enum


class Regulation(str, Enum):
    GDPR    = "gdpr_dsgvo"
    LKSG    = "lksg"
    ENEFG   = "enefg"
    CSRD    = "csrd"
    BDSG    = "bdsg"
    NIS2    = "nis2"
    AI_ACT  = "eu_ai_act"
    HINSCHG = "hinschg"
    ARBSCHG = "arbschg"
    AGG     = "agg"
    MILOG   = "milog"


class Industry(str, Enum):
    IT_SOFTWARE = "it_software"
    MANUFACTURING = "manufacturing"
    HEALTHCARE = "healthcare"
    RETAIL = "retail"
    FINANCE = "finance"
    LOGISTICS = "logistics"
    CONSTRUCTION = "construction"
    ENERGY = "energy"
    FOOD_BEVERAGE = "food_beverage"
    CONSULTING = "consulting"
    OTHER = "other"


class ObligationType(str, Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    MAY = "MAY"


class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    CANNOT_ASSESS = "CANNOT_ASSESS"


class Priority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AnalysisStep(str, Enum):
    PROFILE_VALIDATION = "profile_validation"
    APPLICABILITY_DETERMINATION = "applicability_determination"
    ARTICLE_RETRIEVAL = "article_retrieval"
    GAP_ANALYSIS = "gap_analysis"
    ACTION_PLAN = "action_plan"
    REPORT_ASSEMBLY = "report_assembly"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
