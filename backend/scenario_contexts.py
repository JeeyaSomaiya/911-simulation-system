from models import ScenarioType
import random

def load_scenario_contexts():
    return {
        ScenarioType.TRAFFIC_ACCIDENT_10_01: [
            {
                "location": "Cranston Ave SE / Deerfoot Tr SE",
                "caller_name": "Broderick Greene", 
                "phone": "403-561-9988",
                "situation": "Witnessed a rollover accident. White SUV is currently in the ditch off southbound Deerfoot Trail just south of Cranston Ave SE. Vehicle appears to have rolled over due to black ice conditions.",
                "current_status": "Drive-by caller who has already left the scene. Observed the accident about 1 minute ago. Driver appears to be injured and trapped in the overturned vehicle.",
                "caller_background": "Excited drive-by caller who witnessed the accident while driving. Not at scene anymore but concerned about the driver's safety.",
                "initial_response": "There's been a bad accident!"
            },
            {
                "location": "Memorial Dr NW / 19 St NW",
                "caller_name": "Sarah Mitchell", 
                "phone": "403-555-7234",
                "situation": "Multi-vehicle collision involving three cars. Front car stopped suddenly, causing chain reaction. Two vehicles have significant front/rear damage.",
                "current_status": "All drivers are out of vehicles and appear conscious. Traffic is completely blocked eastbound on Memorial Drive. Some people seem shaken up.",
                "caller_background": "Pedestrian witness who saw the accident from the sidewalk. Stopped to help and call 911.",
                "initial_response": "There's been a three-car accident."
            }
        ],
        ScenarioType.TRAFFIC_ACCIDENT_10_02: {
            "location": "10 AV SW / 16 ST SW",
            "caller_name": "Candy Wise", 
            "phone": "587-543-6789",
            "situation": "Non-injury accident - one vehicle rear ended another at intersection. Both vehicles still drivable.",
            "current_status": "Drivers are exchanging information. Traffic backing up but no injuries reported.",
            "caller_background": "Witness who saw the accident but didn't stop. Vague about location details.",
            "initial_response": "I just saw a car accident!"
        },
        ScenarioType.ROBBERY_10_30: {
            "location": "South Centre Mall, 100 Anderson Rd SE",
            "caller_name": "Tony Hilson", 
            "phone": "403-665-8532",
            "situation": "Just found a male bleeding outside Safeway; says he was stabbed and robbed of his wallet and phone.",
            "current_status": "Victim is conscious but bleeding from his arm. Suspect described as white male, 25yrs old, 6', slim build, wearing white baseball cap, green hoody, blue jeans. Last seen running towards Anderson Rd through mall parking lot.",
            "caller_background": "Bystander who found the victim. Upset but trying to help. Applying pressure to wound while on call.",
            "initial_response": "I found someone bleeding!"
        },
        ScenarioType.HOME_INVASION_10_08H: {
            "location": "33 Brightondale Pr SE",
            "caller_name": "Tony Hernandez", 
            "phone": "403-483-4384",
            "situation": "Two men kicked down the door and invaded home. Used bear spray and knife. Stole laptop.",
            "current_status": "Caller hiding in bedroom. Intruders just left but might return. Caller's eyes burning from bear spray. Home trashed.",
            "caller_background": "Homeowner terrified for safety. Hiding and afraid intruders might come back.",
            "initial_response": "Intruders broke into my home!"
        },
        ScenarioType.IMPAIRED_DRIVER_10_83: {
            "location": "Stoney Trail/Country Hills BV",
            "caller_name": "Betty Jensen", 
            "phone": "403-562-1159",
            "situation": "Observing vehicle swerving erratically, hitting brakes randomly, unable to stay in lanes.",
            "current_status": "Following vehicle eastbound on Stoney Trail. Driver appears impaired. Red VW Golf, license BJR5561.",
            "caller_background": "Concerned driver returning from Banff to Airdrie. Insistent on following vehicle despite safety concerns.",
            "initial_response": "I'm seeing a dangerous driver!"
        },
        ScenarioType.GAS_THEFT_10_34: {
            "location": "7-11 Woodbine, 460 Woodbine BV SW",
            "caller_name": "Janine Shotbothsides", 
            "phone": "403-250-2374",
            "situation": "Vehicle drove off without paying for $82.39 worth of gas.",
            "current_status": "Red pickup truck with license BPT5789 fled scene turning right toward 24 St. Driver: WM, late 20s, baseball cap, grey winter jacket.",
            "caller_background": "Gas station employee reporting theft. Calm but wants police intervention.",
            "initial_response": "Someone stole gas!"
        },
        ScenarioType.MENTAL_HEALTH_10_21: {
            "location": "N/A - Caller won't provide location",
            "caller_name": "Selena Crock", 
            "phone": "403-271-8645",
            "situation": "Caller reporting feeling watched during shopping trip and noticing suspicious number of red cars.",
            "current_status": "Caller is safe but paranoid. Rambling about people looking at her and red cars being suspicious.",
            "caller_background": "Individual experiencing paranoid thoughts. Refuses to provide location but wants police awareness.",
            "initial_response": "People are acting suspiciously!"
        },
        ScenarioType.SUICIDE_THREAT_10_07: {
            "location": "Unknown",
            "caller_name": "Beth Hunter", 
            "phone": "403-266-4357",
            "situation": "Male caller to distress center threatened to take pills after recent breakup.",
            "current_status": "Caller hung up when told police would be contacted. Identity: Dan Depta, possibly middle-aged, might be drinking.",
            "caller_background": "Distress center employee reporting third-party suicide threat. Cooperative but lacks location information.",
            "initial_response": "A man threatened to kill himself!"
        },
        ScenarioType.TRAFFIC_HAZARD_10_88: {
            "location": "Northbound Deerfoot at 16 Av",
            "caller_name": "Candy Wise", 
            "phone": "403-555-0123",
            "situation": "Car stopped on side of Deerfoot with person inside.",
            "current_status": "Dark SUV parked on shoulder. Driver appears to be a white male in green jacket.",
            "caller_background": "Drive-by caller reporting traffic hazard. Not stopping but concerned about stopped vehicle.",
            "initial_response": "I saw a car stopped on the road!"
        },
        ScenarioType.THEFT_10_34: {
            "location": "705 8 ST SW",
            "caller_name": "Jamal Samsonoff", 
            "phone": "825-834-4672",
            "situation": "Theft from convenience store - suspect grabbed chips and pop and ran away.",
            "current_status": "Suspect ran toward LRT station eastbound. White male, 20-25, 6'0, heavy build, blue shirt, jeans, red shoes.",
            "caller_background": "Store employee reporting theft, upset and wanting immediate police response.",
            "initial_response": "We've been robbed!"
        }
    }

def get_random_scenario_context(scenario_type: ScenarioType):
    all_contexts = load_scenario_contexts()
    contexts_for_type = all_contexts.get(scenario_type, [])
    
    if not contexts_for_type:
        return {
            "location": "Unknown Location",
            "caller_name": "Unknown Caller", 
            "phone": "403-000-0000",
            "situation": "Emergency situation",
            "current_status": "Situation in progress",
            "caller_background": "Caller reporting emergency",
            "initial_response": "There's an emergency."
        }

    if isinstance(contexts_for_type, list):
        return random.choice(contexts_for_type)
    else:
        return contexts_for_type
    