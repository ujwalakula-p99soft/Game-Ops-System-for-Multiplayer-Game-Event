from enum import Enum


class Region(str, Enum):
    INDIA = "India"
    SEA = "SEA"
    EUROPE = "Europe"


class DeviceType(str, Enum):
    ANDROID = "Android"
    IOS = "iOS"
    PC = "PC"
    CONSOLE = "Console"


class GameMode(str, Enum):
    SOLO = "SOLO"
    DUO = "DUO"
    SQUAD = "SQUAD"


class RankTier(str, Enum):
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"
