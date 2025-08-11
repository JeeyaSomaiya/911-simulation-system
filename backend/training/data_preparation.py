import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import random

def generate_sample_training_data():
    """Generate sample training data for the 911 simulation system"""
    
    scenarios = {
        'house_fire': {
            'background': 'House fire with family members potentially trapped',
            'caller_profile': 'adult_female_30s',
            'key_information': {
                'location': '123 Oak Street',
                'occupants': 'family of 4, 2 children upstairs',
                'fire_location': 'kitchen, spreading to living room',
                'access_issues': 'front door blocked by smoke'
            }
        },
        'medical_emergency': {
            'background': 'Chest pain, possible heart attack',
            'caller_profile': 'adult_male_40s',
            'key_information': {
                'patient_age': '67 years old',
                'symptoms': 'chest pain, shortness of breath, sweating',
                'consciousness': 'conscious but in severe pain',
                'medical_history': 'high blood pressure, diabetes'
            }
        },
        'robbery': {
            'background': 'Armed robbery in progress at convenience store',
            'caller_profile': 'adult_female_25s',
            'key_information': {
                'location': 'Quick Stop on Main Street',
                'suspects': '2 males, both with handguns',
                'victims': 'store clerk and 2 customers',
                'suspect_description': 'one tall wearing black hoodie, one short with red cap'
            }
        }
    }
    
    conversations = []
    
    # Generate conversations for each scenario
    for scenario_type, scenario_data in scenarios.items():
        for i in range(10):  # 10 conversations per scenario
            conversation = generate_conversation(scenario_type, scenario_data, i)
            conversations.append(conversation)
    
    return conversations

def generate_conversation(scenario_type: str, scenario_data: Dict, variation: int) -> Dict[str, Any]:
    """Generate a single conversation for training"""
    
    conversation_id = str(uuid.uuid4())
    
    # Define emotional progression patterns
    emotional_progressions = [
        [('PANICKED', 9), ('PANICKED', 8), ('WORRIED', 6), ('WORRIED', 5), ('CALM', 3)],
        [('HYSTERICAL', 10), ('PANICKED', 8), ('PANICKED', 7), ('WORRIED', 5), ('WORRIED', 4)],
        [('WORRIED', 7), ('WORRIED', 6), ('PANICKED', 8), ('WORRIED', 5), ('CALM', 3)],
        [('PANICKED', 8), ('WORRIED', 6), ('WORRIED', 5), ('RELIEVED', 3), ('CALM', 2)]
    ]
    
    progression = emotional_progressions[variation % len(emotional_progressions)]
    
    # Generate conversation turns based on scenario
    if scenario_type == 'house_fire':
        turns = generate_house_fire_conversation(scenario_data, progression)
    elif scenario_type == 'medical_emergency':
        turns = generate_medical_conversation(scenario_data, progression)
    else:  # robbery
        turns = generate_robbery_conversation(scenario_data, progression)
    
    # Build emotional progression timeline
    emotional_timeline = []
    for i, (state, intensity) in enumerate(progression):
        emotional_timeline.append({
            'turn': i + 1,
            'state': state,
            'intensity': intensity,
            'timestamp': i * 15  # 15 seconds between emotional changes
        })
    
    return {
        'conversation_id': conversation_id,
        'scenario_type': scenario_type,
        'emotional_progression': emotional_timeline,
        'context': {
            'caller_demographics': scenario_data['caller_profile'],
            'emergency_details': scenario_data['key_information'],
            'location_type': 'residential' if scenario_type == 'house_fire' else 'commercial'
        },
        'conversation': turns
    }

def generate_house_fire_conversation(scenario_data: Dict, emotional_progression: List) -> List[Dict]:
    """Generate house fire conversation"""
    
    turns = [
        {
            'role': 'dispatcher',
            'content': '911, what\'s your emergency?',
            'timestamp': 0
        },
        {
            'role': 'caller',
            'content': 'Oh my God, there\'s a fire! My house is on fire!',
            'emotional_state': emotional_progression[0][0],
            'intensity': emotional_progression[0][1],
            'timestamp': 2.1
        },
        {
            'role': 'dispatcher',
            'content': 'Okay, I need you to stay calm. What\'s your address?',
            'timestamp': 5.2
        },
        {
            'role': 'caller',
            'content': 'It\'s 123 Oak Street! Please hurry, my kids are upstairs!',
            'emotional_state': emotional_progression[1][0],
            'intensity': emotional_progression[1][1],
            'timestamp': 8.5
        },
        {
            'role': 'dispatcher',
            'content': 'Fire department is on the way. Are you and your children able to get out safely?',
            'timestamp': 12.8
        },
        {
            'role': 'caller',
            'content': 'I can\'t get upstairs! The smoke is too thick! They\'re trapped!',
            'emotional_state': emotional_progression[2][0],
            'intensity': emotional_progression[2][1],
            'timestamp': 16.2
        },
        {
            'role': 'dispatcher',
            'content': 'Listen to me carefully. Do not try to go upstairs. Get yourself out of the house immediately. Can you do that?',
            'timestamp': 21.5
        },
        {
            'role': 'caller',
            'content': 'But my babies are up there! I can\'t leave them!',
            'emotional_state': emotional_progression[3][0],
            'intensity': emotional_progression[3][1],
            'timestamp': 25.1
        },
        {
            'role': 'dispatcher',
            'content': 'The firefighters will get your children. You need to get out now so they can do their job. Are you moving toward an exit?',
            'timestamp': 30.3
        },
        {
            'role': 'caller',
            'content': 'Okay, okay... I\'m going to the back door. When will they be here?',
            'emotional_state': emotional_progression[4][0],
            'intensity': emotional_progression[4][1],
            'timestamp': 34.7
        }
    ]
    
    return turns

def generate_medical_conversation(scenario_data: Dict, emotional_progression: List) -> List[Dict]:
    """Generate medical emergency conversation"""
    
    turns = [
        {
            'role': 'dispatcher',
            'content': '911, what\'s your emergency?',
            'timestamp': 0
        },
        {
            'role': 'caller',
            'content': 'I need an ambulance! My father is having chest pain!',
            'emotional_state': emotional_progression[0][0],
            'intensity': emotional_progression[0][1],
            'timestamp': 2.8
        },
        {
            'role': 'dispatcher',
            'content': 'Okay, what\'s your location?',
            'timestamp': 6.1
        },
        {
            'role': 'caller',
            'content': 'We\'re at 456 Maple Drive. He\'s sweating and says his chest really hurts.',
            'emotional_state': emotional_progression[1][0],
            'intensity': emotional_progression[1][1],
            'timestamp': 9.4
        },
        {
            'role': 'dispatcher',
            'content': 'How old is your father?',
            'timestamp': 14.2
        },
        {
            'role': 'caller',
            'content': 'He\'s 67. He has high blood pressure and diabetes.',
            'emotional_state': emotional_progression[2][0],
            'intensity': emotional_progression[2][1],
            'timestamp': 17.8
        },
        {
            'role': 'dispatcher',
            'content': 'Is he conscious and breathing?',
            'timestamp': 21.5
        },
        {
            'role': 'caller',
            'content': 'Yes, he\'s awake but he looks really pale. Should I give him his heart medication?',
            'emotional_state': emotional_progression[3][0],
            'intensity': emotional_progression[3][1],
            'timestamp': 25.2
        },
        {
            'role': 'dispatcher',
            'content': 'Don\'t give him any medication unless he normally takes nitroglycerin for his heart. The paramedics are on their way.',
            'timestamp': 30.7
        },
        {
            'role': 'caller',
            'content': 'Okay, thank you. How long until they get here?',
            'emotional_state': emotional_progression[4][0],
            'intensity': emotional_progression[4][1],
            'timestamp': 35.1
        }
    ]
    
    return turns

def generate_robbery_conversation(scenario_data: Dict, emotional_progression: List) -> List[Dict]:
    """Generate robbery conversation"""
    
    turns = [
        {
            'role': 'dispatcher',
            'content': '911, what\'s your emergency?',
            'timestamp': 0
        },
        {
            'role': 'caller',
            'content': 'There\'s a robbery happening right now! Two men with guns!',
            'emotional_state': emotional_progression[0][0],
            'intensity': emotional_progression[0][1],
            'timestamp': 2.5
        },
        {
            'role': 'dispatcher',
            'content': 'Where are you located?',
            'timestamp': 6.8
        },
        {
            'role': 'caller',
            'content': 'Quick Stop on Main Street! They have guns pointed at the clerk!',
            'emotional_state': emotional_progression[1][0],
            'intensity': emotional_progression[1][1],
            'timestamp': 10.2
        },
        {
            'role': 'dispatcher',
            'content': 'Are you in a safe location? Can the suspects see you?',
            'timestamp': 15.1
        },
        {
            'role': 'caller',
            'content': 'I\'m hiding behind the chips aisle. There are other customers here too.',
            'emotional_state': emotional_progression[2][0],
            'intensity': emotional_progression[2][1],
            'timestamp': 19.3
        },
        {
            'role': 'dispatcher',
            'content': 'Stay hidden and stay quiet. Can you describe the suspects?',
            'timestamp': 24.7
        },
        {
            'role': 'caller',
            'content': 'One is tall in a black hoodie, the other is shorter with a red cap. Both have handguns.',
            'emotional_state': emotional_progression[3][0],
            'intensity': emotional_progression[3][1],
            'timestamp': 29.1
        },
        {
            'role': 'dispatcher',
            'content': 'Police are on their way. Stay where you are and don\'t try to be a hero. Are the suspects still inside?',
            'timestamp': 35.4
        },
        {
            'role': 'caller',
            'content': 'Yes, they\'re still at the counter. I think they\'re taking money from the register.',
            'emotional_state': emotional_progression[4][0],
            'intensity': emotional_progression[4][1],
            'timestamp': 40.2
        }
    ]
    
    return turns

def save_training_data(conversations: List[Dict], filename: str = 'sample_training_data.json'):
    """Save training data to file"""
    
    with open(f'./data/training_datasets/{filename}', 'w') as f:
        json.dump(conversations, f, indent=2)
    
    print(f"Saved {len(conversations)} conversations to {filename}")

if __name__ == '__main__':
    # Generate and save sample training data
    conversations = generate_sample_training_data()
    save_training_data(conversations)
    
    print("Sample training data generated successfully!")
    print(f"Generated {len(conversations)} conversations across {len(set(c['scenario_type'] for c in conversations))} scenarios")
