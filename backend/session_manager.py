import uuid
from datetime import datetime
from typing import Optional

from models import SessionData, CallerState, ScenarioType, EmotionalState
from scenario_contexts import get_random_scenario_context

sessions = {}

class SessionManager:
    def create_session(self, trainee_id: str, scenario_type: str) -> SessionData:
        session_id = str(uuid.uuid4())
        scenario_map = {
            "10-01": ScenarioType.TRAFFIC_ACCIDENT_10_01,
            "10-02": ScenarioType.TRAFFIC_ACCIDENT_10_02,
            "10-03": ScenarioType.MISC_INDUSTRIAL_10_03,
            "10-04": ScenarioType.ALARM_10_04,
            "10-04-video": ScenarioType.ALARM_VIDEO_10_04,
            "10-05": ScenarioType.ASSAULT_10_05,
            "10-06": ScenarioType.ASSISTANCE_10_06,
            "10-07": ScenarioType.SUICIDE_THREAT_10_07,
            "10-08": ScenarioType.BREAK_ENTER_10_08,
            "10-08H": ScenarioType.HOME_INVASION_10_08H,
            "10-09": ScenarioType.HOME_INVASION_10_09,
            "10-10": ScenarioType.ANIMAL_10_10,
            "10-11": ScenarioType.DOMESTIC_10_11,
            "10-11-standby": ScenarioType.DOMESTIC_STANDBY_10_11,
            "10-12": ScenarioType.DRUNK_DISTURBANCE_10_12,
            "10-13": ScenarioType.ESCORT_10_13,
            "10-14": ScenarioType.DISTURBANCE_10_14,
            "10-15": ScenarioType.FIRE_10_15,
            "10-16": ScenarioType.FRAUD_10_16,
            "10-17": ScenarioType.INDECENT_ACT_10_17,
            "10-20": ScenarioType.LOST_FOUND_10_20,
            "10-20-package": ScenarioType.SUSPICIOUS_PACKAGE_10_20,
            "10-20-explosive": ScenarioType.EXPLOSIVE_10_20,
            "10-21": ScenarioType.MENTAL_HEALTH_10_21,
            "10-22": ScenarioType.MISSING_PERSON_10_22,
            "10-24": ScenarioType.NOISE_PARTY_10_24,
            "10-26": ScenarioType.ESCAPED_PRISONER_10_26,
            "10-27": ScenarioType.PROPERTY_DAMAGE_10_27,
            "10-27-contamination": ScenarioType.PRODUCT_CONTAMINATION_10_27,
            "10-30": ScenarioType.ROBBERY_10_30,
            "10-31": ScenarioType.SHOPLIFTING_10_31,
            "10-32": ScenarioType.SUDDEN_DEATH_10_32,
            "10-33": ScenarioType.SUSPICIOUS_PERSON_10_33,
            "10-33-panhandling": ScenarioType.PANHANDLING_10_33,
            "10-34": ScenarioType.THEFT_10_34,
            "10-35": ScenarioType.THREATS_10_35,
            "10-36": ScenarioType.SEXUAL_ASSAULT_10_36,
            "10-37": ScenarioType.MEDICAL_COLLAPSE_10_37,
            "10-38": ScenarioType.DRUGS_10_38,
            "10-39": ScenarioType.NOISE_EXCESSIVE_10_39,
            "10-40": ScenarioType.GUNSHOTS_10_40,
            "10-41": ScenarioType.UNWANTED_GUEST_10_41,
            "10-42": ScenarioType.HARASSMENT_10_42,
            "10-43": ScenarioType.WELFARE_CHECK_10_43,
            "10-43-abuse": ScenarioType.ABUSE_10_43,
            "10-43-peace": ScenarioType.KEEP_PEACE_10_43,
            "10-43-danger": ScenarioType.IMMINENT_DANGER_10_43,
            "10-43-unknown": ScenarioType.UNKNOWN_THIRD_PARTY_10_43,
            "10-44": ScenarioType.ABDUCTION_10_44,
            "10-44-parental": ScenarioType.PARENTAL_ABDUCTION_10_44,
            "10-45": ScenarioType.NOTIFICATION_10_45,
            "10-47": ScenarioType.CHILD_CUSTODY_10_47,
            "10-53": ScenarioType.WANTED_10_53,
            "10-53-mental": ScenarioType.MENTAL_WARRANT_10_53,
            "10-53-ual": ScenarioType.UAL_WARRANT_10_53,
            "10-69": ScenarioType.PROSTITUTION_10_69,
            "10-81": ScenarioType.ABANDONED_AUTO_10_81,
            "10-82": ScenarioType.CARELESS_DRIVER_10_82,
            "10-82-rage": ScenarioType.ROAD_RAGE_10_82,
            "10-83": ScenarioType.IMPAIRED_DRIVER_10_83,
            "10-84": ScenarioType.HIT_AND_RUN_10_84,
            "10-85": ScenarioType.SPEEDER_10_85,
            "10-86": ScenarioType.STOLEN_AUTO_10_86,
            "10-86-recovered": ScenarioType.RECOVERED_AUTO_10_86,
            "10-87": ScenarioType.SUSPICIOUS_VEHICLE_10_87,
            "10-88": ScenarioType.TRAFFIC_HAZARD_10_88,
            "10-91": ScenarioType.HAZMAT_SPILL_10_91,
            "10-92": ScenarioType.AIRCRAFT_INCIDENT_10_92,
            "10-93": ScenarioType.ACT_OF_NATURE_10_93,
            "10-97": ScenarioType.LURING_10_97,
            "X99": ScenarioType.MISCELLANEOUS_X99,
            "100": ScenarioType.BANK_HOLDUP_100,
            "200": ScenarioType.OFFICER_TROUBLE_200,
            "300": ScenarioType.FIREARM_300,
            "300-shots": ScenarioType.SHOTS_FIRED_300,
            "300-hostage": ScenarioType.HOSTAGE_300,
            "300-victim": ScenarioType.SHOOTING_VICTIM_300,
            "300-assailant": ScenarioType.ACTIVE_ASSAILANT_300,
            "400": ScenarioType.BOMB_THREAT_400,
            "400-found": ScenarioType.EXPLOSIVE_FOUND_400,
            "400-explosion": ScenarioType.EXPLOSION_400,
            "500": ScenarioType.EXTORTION_500,
            "800": ScenarioType.AIRCRAFT_HIJACK_800,
            "1000": ScenarioType.PUBLIC_SAFETY_1000,
            "2000": ScenarioType.MAJOR_INCIDENT_2000,
            "5000": ScenarioType.PRISON_RIOT_5000,
            "5000-blue": ScenarioType.PRISON_BLUE_5000,
            "10-34-gas": ScenarioType.GAS_THEFT_10_34,
            "10-30-stab": ScenarioType.ROBBERY_10_30
        }
        
        scenario_enum = scenario_map.get(scenario_type, ScenarioType.TRAFFIC_ACCIDENT_10_01)
        
        initial_intensity = 9 if scenario_enum in [
            ScenarioType.ROBBERY_10_30, 
            ScenarioType.HOME_INVASION_10_08H,
            ScenarioType.HOME_INVASION_10_09,
            ScenarioType.BREAK_ENTER_10_08,
            ScenarioType.ASSAULT_10_05,
            ScenarioType.SEXUAL_ASSAULT_10_36,
            ScenarioType.GUNSHOTS_10_40,
            ScenarioType.FIREARM_300,
            ScenarioType.SHOTS_FIRED_300,
            ScenarioType.HOSTAGE_300,
            ScenarioType.SHOOTING_VICTIM_300,
            ScenarioType.ACTIVE_ASSAILANT_300,
            ScenarioType.BANK_HOLDUP_100,
            ScenarioType.OFFICER_TROUBLE_200,
            ScenarioType.ABDUCTION_10_44,
            ScenarioType.PARENTAL_ABDUCTION_10_44,
            ScenarioType.SUICIDE_THREAT_10_07,
            ScenarioType.BOMB_THREAT_400,
            ScenarioType.EXPLOSIVE_FOUND_400,
            ScenarioType.EXPLOSION_400
        ] else 7
        initial_emotion = EmotionalState.PANICKED if initial_intensity > 7 else EmotionalState.WORRIED
        
        selected_context = get_random_scenario_context(scenario_enum)
        
        initial_state = CallerState(
            emotional_state=initial_emotion,
            intensity=initial_intensity,
            scenario_type=scenario_enum,
            key_details_revealed=[],
            conversation_history=[],
            caller_profile={
                "scenario": scenario_type,
                "selected_context": selected_context
            },
            scenario_progress=0.0
        )
        
        session = SessionData(
            session_id=session_id,
            trainee_id=trainee_id,
            scenario_type=scenario_enum,
            caller_state=initial_state,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            is_active=True
        )
        
        sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        return sessions.get(session_id)
    
    def update_session(self, session_id: str, caller_state: CallerState):
        if session_id in sessions:
            sessions[session_id].caller_state = caller_state
            sessions[session_id].last_activity = datetime.now()
    
    def terminate_session(self, session_id: str):
        if session_id in sessions:
            sessions[session_id].is_active = False
            