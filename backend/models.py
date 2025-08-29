from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class EmotionalState(Enum):
    CALM = "calm"
    WORRIED = "worried"
    PANICKED = "panicked"
    HYSTERICAL = "hysterical"
    RELIEVED = "relieved"

class ScenarioType(Enum):
    TRAFFIC_ACCIDENT_10_01 = "10-01"
    TRAFFIC_ACCIDENT_10_02 = "10-02"
    MISC_INDUSTRIAL_10_03 = "10-03"
    ALARM_10_04 = "10-04"
    ALARM_VIDEO_10_04 = "10-04-video"
    ASSAULT_10_05 = "10-05"
    ASSISTANCE_10_06 = "10-06"
    SUICIDE_THREAT_10_07 = "10-07"
    BREAK_ENTER_10_08 = "10-08"
    HOME_INVASION_10_08H = "10-08H"
    HOME_INVASION_10_09 = "10-09"
    ANIMAL_10_10 = "10-10"
    DOMESTIC_10_11 = "10-11"
    DOMESTIC_STANDBY_10_11 = "10-11-standby"
    DRUNK_DISTURBANCE_10_12 = "10-12"
    ESCORT_10_13 = "10-13"
    DISTURBANCE_10_14 = "10-14"
    FIRE_10_15 = "10-15"
    FRAUD_10_16 = "10-16"
    INDECENT_ACT_10_17 = "10-17"
    LOST_FOUND_10_20 = "10-20"
    SUSPICIOUS_PACKAGE_10_20 = "10-20-package"
    EXPLOSIVE_10_20 = "10-20-explosive"
    MENTAL_HEALTH_10_21 = "10-21"
    MISSING_PERSON_10_22 = "10-22"
    NOISE_PARTY_10_24 = "10-24"
    ESCAPED_PRISONER_10_26 = "10-26"
    PROPERTY_DAMAGE_10_27 = "10-27"
    PRODUCT_CONTAMINATION_10_27 = "10-27-contamination"
    ROBBERY_10_30 = "10-30"
    SHOPLIFTING_10_31 = "10-31"
    SUDDEN_DEATH_10_32 = "10-32"
    SUSPICIOUS_PERSON_10_33 = "10-33"
    PANHANDLING_10_33 = "10-33-panhandling"
    THEFT_10_34 = "10-34"
    GAS_THEFT_10_34 = "10-34-gas"
    THREATS_10_35 = "10-35"
    SEXUAL_ASSAULT_10_36 = "10-36"
    MEDICAL_COLLAPSE_10_37 = "10-37"
    DRUGS_10_38 = "10-38"
    NOISE_EXCESSIVE_10_39 = "10-39"
    GUNSHOTS_10_40 = "10-40"
    UNWANTED_GUEST_10_41 = "10-41"
    HARASSMENT_10_42 = "10-42"
    WELFARE_CHECK_10_43 = "10-43"
    ABUSE_10_43 = "10-43-abuse"
    KEEP_PEACE_10_43 = "10-43-peace"
    IMMINENT_DANGER_10_43 = "10-43-danger"
    UNKNOWN_THIRD_PARTY_10_43 = "10-43-unknown"
    ABDUCTION_10_44 = "10-44"
    PARENTAL_ABDUCTION_10_44 = "10-44-parental"
    NOTIFICATION_10_45 = "10-45"
    CHILD_CUSTODY_10_47 = "10-47"
    WANTED_10_53 = "10-53"
    MENTAL_WARRANT_10_53 = "10-53-mental"
    UAL_WARRANT_10_53 = "10-53-ual"
    PROSTITUTION_10_69 = "10-69"
    ABANDONED_AUTO_10_81 = "10-81"
    CARELESS_DRIVER_10_82 = "10-82"
    ROAD_RAGE_10_82 = "10-82-rage"
    IMPAIRED_DRIVER_10_83 = "10-83"
    HIT_AND_RUN_10_84 = "10-84"
    SPEEDER_10_85 = "10-85"
    STOLEN_AUTO_10_86 = "10-86"
    RECOVERED_AUTO_10_86 = "10-86-recovered"
    SUSPICIOUS_VEHICLE_10_87 = "10-87"
    TRAFFIC_HAZARD_10_88 = "10-88"
    HAZMAT_SPILL_10_91 = "10-91"
    AIRCRAFT_INCIDENT_10_92 = "10-92"
    ACT_OF_NATURE_10_93 = "10-93"
    LURING_10_97 = "10-97"
    MISCELLANEOUS_X99 = "X99"
    BANK_HOLDUP_100 = "100"
    OFFICER_TROUBLE_200 = "200"
    FIREARM_300 = "300"
    SHOTS_FIRED_300 = "300-shots"
    HOSTAGE_300 = "300-hostage"
    SHOOTING_VICTIM_300 = "300-victim"
    ACTIVE_ASSAILANT_300 = "300-assailant"
    BOMB_THREAT_400 = "400"
    EXPLOSIVE_FOUND_400 = "400-found"
    EXPLOSION_400 = "400-explosion"
    EXTORTION_500 = "500"
    AIRCRAFT_HIJACK_800 = "800"
    PUBLIC_SAFETY_1000 = "1000"
    MAJOR_INCIDENT_2000 = "2000"
    PRISON_RIOT_5000 = "5000"
    PRISON_BLUE_5000 = "5000-blue"

@dataclass
class CallerState:
    emotional_state: EmotionalState
    intensity: int
    scenario_type: ScenarioType
    key_details_revealed: List[str]
    conversation_history: List[Dict[str, str]]
    caller_profile: Dict[str, Any]
    scenario_progress: float

@dataclass
class SessionData:
    session_id: str
    trainee_id: str
    scenario_type: ScenarioType
    caller_state: CallerState
    created_at: datetime
    last_activity: datetime
    is_active: bool
    