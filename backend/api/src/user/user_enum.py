from enum import Enum

class UserRoleEnum(str, Enum):
    USER = "USER"
    THERAPIST = "THERAPIST"
    ADMIN = "ADMIN"