"""Application constants, enums, and allowed domain values."""

from enum import Enum, IntEnum


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class UserRole(str, Enum):
    LEARNER = "learner"
    EDUCATOR = "educator"
    ADMIN = "admin"


class PreferredLanguage(str, Enum):
    ODIA = "odia"
    ENGLISH = "english"


class ExamTarget(str, Enum):
    CHSE_CLASS_12 = "chse_class_12"
    JEE_MAIN = "jee_main"
    NEET_UG = "neet_ug"


class ClassLevel(IntEnum):
    CLASS_9 = 9
    CLASS_10 = 10
    CLASS_12 = 12

    @classmethod
    def values(cls) -> list[int]:
        return [c.value for c in cls]


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    NUMERICAL = "numerical"


class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ApprovalState(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"


class VariantPurpose(str, Enum):
    ODIA = "odia"
    SIMPLIFIED = "simplified"
    UNTIMED = "untimed"
    PREREQUISITE = "prerequisite"
    TRANSFER = "transfer"
    TERMINOLOGY_BRIDGE = "terminology_bridge"


class AttemptLifecycle(str, Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    ABANDONED = "abandoned"


class StudyPlanStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
