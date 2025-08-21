import json
import random
import os
from models import ScenarioType

def load_json_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def get_random_name_and_phone():
    names_data = load_json_data('data/names.json')
    numbers_data = load_json_data('data/numbers.json')
    
    if names_data and numbers_data:
        all_names = names_data.get('male_names', []) + names_data.get('female_names', [])
        phone_numbers = numbers_data.get('phone_numbers', [])
        
        if all_names and phone_numbers:
            return random.choice(all_names), random.choice(phone_numbers)
    
    return "Unknown Caller", "403-000-0000"

def load_scenario_contexts():
    return {
        ScenarioType.TRAFFIC_ACCIDENT_10_01: [
            {
                "location": "Cranston Ave SE / Deerfoot Tr SE",
                "situation": "Witnessed a rollover accident. White SUV is currently in the ditch off southbound Deerfoot Trail just south of Cranston Ave SE. Vehicle appears to have rolled over due to black ice conditions.",
                "current_status": "Drive-by caller who has already left the scene. Observed the accident about 1 minute ago. Driver appears to be injured and trapped in the overturned vehicle.",
                "caller_background": "Excited drive-by witness who saw the accident while driving. Not at scene anymore but concerned about the driver's safety."
            },
            {
                "location": "Memorial Dr NW / 19 St NW",
                "situation": "Multi-vehicle collision involving three cars. Front car stopped suddenly, causing chain reaction. Two vehicles have significant front/rear damage.",
                "current_status": "All drivers are out of vehicles and appear conscious. Traffic is completely blocked eastbound on Memorial Drive. Some people seem shaken up.",
                "caller_background": "Pedestrian witness who saw the accident from the sidewalk. Stopped to help and call 911."
            }
        ],
        ScenarioType.TRAFFIC_ACCIDENT_10_02: [
            {
                "location": "Macleod Trail SE / 12 Avenue SE",
                "situation": "Non-injury accident - one vehicle ran into the side of another at the intersection. Vehicles are not driveable, occurred in the middle of the intersection. Traffic is blocked going northbound. Grey sedan and green hatchback involved.",
                "current_status": "Both cars are still in the intersection. Traffic backing up northbound but no injuries reported.",
                "caller_background": "Witness who saw the accident while driving by in their car."
            },
            {
                "location": "Stoney Trail / 16 Avenue NE",
                "situation": "Non-injury accident - Red Dodge Ram with license plate CCB9173 side swiped a grey Nissan Murano with license plate HRG8156 coming off the ramp on Stoney trail. Both vehicles are drivable, traffic is not blocked.",
                "current_status": "Both cars pulled over on the shoulder of Stoney trail, no traffic being backed up.",
                "caller_background": "Driver of the Nissan Murano (victim who got side swiped), is angry about the situation."
            },
            {
                "location": "Shaganappi Trail / Bowness Road NW",
                "situation": "Non-injury accident - Brown Ford car with license plate BBK9203 turned the corner into an Audi Q4 with license plate KWP681. Both vehicles are drivable, right lane of traffic is blocked.",
                "current_status": "Both cars are pulled over in the right lane of westbound Bowness Road. Right lane of traffic being blocked.",
                "caller_background": "Driver of the Audi Q4 (victim who got hit), is panicked."
            },
            {
                "location": "Address: 4611 14 Street NW, Name: the Winter Club",
                "situation": "Non-injury accident - Black Honda CRV with license plate BKP9750 backed into a grey Toyota RAV4 with license plate GAP837 while reversing out of a parking spot in a parking lot. Both vehicles are drivable, no traffic is blocked.",
                "current_status": "Both cars are stopped in the parking lot, traffic can get around, no traffic blocked.",
                "caller_background": "Driver of the Toyota RAV4 (victim who got backed into), is frustrated."
            },
            {
                "location": "Centre Street / 56 Avenue NE",
                "situation": "Non-injury accident - White Volkswagen Golf with license plate HOU7689 rear-ended a red Mazda 3 with license plate HUY7510 when the Mazda 3 braked hard. Vehicles are not drivable, traffic is blocked on the left lane of Northbound Centre Street.",
                "current_status": "Both cars are stopped in the left lane of Centre Street, traffic is blocked in the left lane. Volkswagen Golf is leaking fluids.",
                "caller_background": "Driver of the Volkswagen Golf (at-fault driver who rear-ended the other car), is panicked."
            },
            {
                "location": "Fairmount Drive SE",
                "situation": "Non-injury accident - Red Honda CRV with license plate PQI863 skid on a patch of ice and hit the median. Car's wheel is pushed out of position. Vehicle is not drivable. Traffic is blocked in the left lane of northbound Fairmount Drive.",
                "current_status": "Car stopped against the median of the left lane of Fairmount Drive. Traffic is blocked in the left lane. Car's wheel is out of place.",
                "caller_background": "Driver of the Honda CRV (single vehicle accident victim), is panicked."
            },
            {
                "location": "96 Ave SW / Hillgrove Drive SW",
                "situation": "Non-injury accident - Red Toyota Camry with license plate DHT294 drove through a stop sign and ran into the side of a black Honda Accord with license plate QXM872 (T-bone accident). Intersection is blocked, vehicles are not drivable. Traffic is blocked around the intersection.",
                "current_status": "Both vehicles stopped in the intersection. Traffic is blocked around the intersection.",
                "caller_background": "Driver of the Honda Accord (victim who got T-boned), is frustrated."
            },
            {
                "location": "Deerfoot Trail / McKnight Boulevard NE ",
                "situation": "Non-injury accident - stop and go traffic on Deerfoot trail, White Ford F-150 with license plate JLK321 rear-ended a blue Chevrolet Malibu with license plate RNS430. Both vehicles are drivable and pulled over to the shoulder of northbound Deerfoot trail.",
                "current_status": "Both vehicles pulled over to the shoulder of northbound Deerfoot, no traffic is blocked.",
                "caller_background": "Driver of the Chevrolet Malibu (victim who got rear-ended)"
            },
            {
                "location": "35 Ave SW near Glenpatrick Dr SW",
                "situation": "Non-injury accident - Silver Nissan Altima with license plate TEW908 was skidding on ice, lost control, and crashed into a pole. Vehicle is not drivable. Traffic can get around, traffic is not blocked.",
                "current_status": "Vehicle is still against the pole to the left of the road. Car is not drivable. No traffic is blocked.",
                "caller_background": "Driver of the Nissan Altima (single vehicle accident victim), is panicked."
            }
        ],
        ScenarioType.ROBBERY_10_30: {
            "location": "South Centre Mall, 100 Anderson Rd SE",
            "situation": "Just found a male bleeding outside Safeway; says he was stabbed and robbed of his wallet and phone.",
            "current_status": "Victim is conscious but bleeding from his arm. Suspect described as white male, 25yrs old, 6', slim build, wearing white baseball cap, green hoody, blue jeans. Last seen running towards Anderson Rd through mall parking lot.",
            "caller_background": "Bystander who found the victim. Upset but trying to help. Applying pressure to wound while on call."
        },
        ScenarioType.HOME_INVASION_10_08H: {
            "location": "33 Brightondale Pr SE",
            "situation": "Two men kicked down the door and invaded home. Used bear spray and knife. Stole laptop.",
            "current_status": "Caller hiding in bedroom. Intruders just left but might return. Caller's eyes burning from bear spray. Home trashed.",
            "caller_background": "Homeowner terrified for safety. Hiding and afraid intruders might come back."
        },
        ScenarioType.IMPAIRED_DRIVER_10_83: {
            "location": "Stoney Trail/Country Hills BV",
            "situation": "Observing vehicle swerving erratically, hitting brakes randomly, unable to stay in lanes.",
            "current_status": "Following vehicle eastbound on Stoney Trail. Driver appears impaired. Red VW Golf, license BJR5561.",
            "caller_background": "Concerned driver returning from Banff to Airdrie. Insistent on following vehicle despite safety concerns."
        },
        ScenarioType.GAS_THEFT_10_34: {
            "location": "7-11 Woodbine, 460 Woodbine BV SW",
            "situation": "Vehicle drove off without paying for $82.39 worth of gas.",
            "current_status": "Red pickup truck with license BPT5789 fled scene turning right toward 24 St. Driver: WM, late 20s, baseball cap, grey winter jacket.",
            "caller_background": "Gas station employee reporting theft. Calm but wants police intervention."
        },
        ScenarioType.MENTAL_HEALTH_10_21: {
            "location": "N/A - Caller won't provide location",
            "situation": "Caller reporting feeling watched during shopping trip and noticing suspicious number of red cars.",
            "current_status": "Caller is safe but paranoid. Rambling about people looking at her and red cars being suspicious.",
            "caller_background": "Individual experiencing paranoid thoughts. Refuses to provide location but wants police awareness."
        },
        ScenarioType.SUICIDE_THREAT_10_07: {
            "location": "Unknown",
            "situation": "Male caller to distress center threatened to take pills after recent breakup.",
            "current_status": "Caller hung up when told police would be contacted. Identity: Dan Depta, possibly middle-aged, might be drinking.",
            "caller_background": "Distress center employee reporting third-party suicide threat. Cooperative but lacks location information."
        },
        ScenarioType.TRAFFIC_HAZARD_10_88: {
            "location": "Northbound Deerfoot at 16 Av",
            "situation": "Car stopped on side of Deerfoot with person inside.",
            "current_status": "Dark SUV parked on shoulder. Driver appears to be a white male in green jacket.",
            "caller_background": "Drive-by caller reporting traffic hazard. Not stopping but concerned about stopped vehicle."
        },
        ScenarioType.THEFT_10_34: {
            "location": "705 8 ST SW",
            "situation": "Theft from convenience store - suspect grabbed chips and pop and ran away.",
            "current_status": "Suspect ran toward LRT station eastbound. White male, 20-25, 6'0, heavy build, blue shirt, jeans, red shoes.",
            "caller_background": "Store employee reporting theft, upset and wanting immediate police response."
        }
    }

def get_random_scenario_context(scenario_type: ScenarioType):
    all_contexts = load_scenario_contexts()
    contexts_for_type = all_contexts.get(scenario_type, [])
    
    if not contexts_for_type:
        caller_name, phone = get_random_name_and_phone()
        return {
            "location": "Unknown Location",
            "caller_name": caller_name,
            "phone": phone,
            "situation": "Emergency situation",
            "current_status": "Situation in progress",
            "caller_background": "Caller reporting emergency"
        }

    if isinstance(contexts_for_type, list):
        selected_context = random.choice(contexts_for_type)
    else:
        selected_context = contexts_for_type
    
    caller_name, phone = get_random_name_and_phone()
    selected_context["caller_name"] = caller_name
    selected_context["phone"] = phone
    
    return selected_context
    