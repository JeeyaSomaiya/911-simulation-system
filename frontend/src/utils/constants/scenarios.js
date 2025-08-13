export const scenarios = [
    {
        "Code": "911",
        "EPD": "",
        "EventType": "911",
        "EventSubtypes": ["VOIP", "hang up/open line", "cell phone pap/hone", "residential", "international"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-01",
        "EPD": "131",
        "EventType": "Accident",
        "EventSubtypes": ["Injury"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-02",
        "EPD": "131",
        "EventType": "Accident",
        "EventSubtypes": ["Non Injury"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-03",
        "EPD": "",
        "EventType": "Miscellaneous",
        "EventSubtypes": ["Other Industrial accident"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-04",
        "EPD": "104",
        "EventType": "Alarm",
        "EventSubtypes": ["ATM", "Commercial", "Res", "Hold Up", "other"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-04",
        "EPD": "110",
        "EventType": "Alarm",
        "EventSubtypes": ["Intrusion with Video"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-05",
        "EPD": "106",
        "EventType": "Assault",
        "EventSubtypes": ["Common"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-06",
        "EPD": "",
        "EventType": "Assistance",
        "EventSubtypes": ["Assist CFD/FMS/Other/Police"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-06",
        "EPD": "",
        "EventType": "Assistance",
        "EventSubtypes": ["Other Police Agency/Peace"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-07",
        "EPD": "127",
        "EventType": "Mental Health",
        "EventSubtypes": ["Suicide"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-08",
        "EPD": "110",
        "EventType": "Break & Enter",
        "EventSubtypes": ["House"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-08H",
        "EPD": "110",
        "EventType": "Break & Enter",
        "EventSubtypes": ["House Invasion"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-09",
        "EPD": "110",
        "EventType": "Break & Enter",
        "EventSubtypes": ["Home Invasion"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-10",
        "EPD": "105",
        "EventType": "Miscellaneous",
        "EventSubtypes": ["Animal complaint"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-11",
        "EPD": "114",
        "EventType": "Domestic",
        "EventSubtypes": ["Domestic"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-11",
        "EPD": "125",
        "EventType": "Domestic",
        "EventSubtypes": ["Stand-by"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-12",
        "EPD": "113",
        "EventType": "Disturbance",
        "EventSubtypes": ["Drunk"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-13",
        "EPD": "",
        "EventType": "Assistance",
        "EventSubtypes": ["Escort/Transport"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-14",
        "EPD": "113",
        "EventType": "Disturbance",
        "EventSubtypes": ["Disturbance"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-15",
        "EPD": "",
        "EventType": "Miscellaneous",
        "EventSubtypes": ["Fire"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-16",
        "EPD": "118",
        "EventType": "Fraud",
        "EventSubtypes": ["General"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-17",
        "EPD": "120",
        "EventType": "Sexual Offences",
        "EventSubtypes": ["Indecent Act (sexual intent)"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-17",
        "EPD": "120",
        "EventType": "Sexual Offences",
        "EventSubtypes": ["Indecent Act (no sexual intent)"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-20",
        "EPD": "103",
        "EventType": "Property",
        "EventSubtypes": ["Lost/Found"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-20",
        "EPD": "108",
        "EventType": "Property",
        "EventSubtypes": ["Suspicious Package"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-20",
        "EPD": "103",
        "EventType": "Property",
        "EventSubtypes": ["Potentially Explosive Object "],
        "WeaponAvailable": true
    },
    {
        "Code": "10-21",
        "EPD": "121",
        "EventType": "Mental Health",
        "EventSubtypes": ["Concern"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-22",
        "EPD": "123",
        "EventType": "Missing Person",
        "EventSubtypes": ["Chronic Runner", "Endangered General", "Group Home", "Medical Absonder", "Suicidal", "Warrant", "Found Person"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-24",
        "EPD": "113",
        "EventType": "Noise",
        "EventSubtypes": ["Noise Party"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-26",
        "EPD": "129",
        "EventType": "Escaped Prisoner",
        "EventSubtypes": ["Escaped Prisoner"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-27",
        "EPD": "111",
        "EventType": "Property Damage",
        "EventSubtypes": ["Property Damage"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-27",
        "EPD": "109",
        "EventType": "Property Damage",
        "EventSubtypes": ["Product Contamination (threat)"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-27",
        "EPD": "108",
        "EventType": "Property Damage",
        "EventSubtypes": ["Product Contamination (suspected/completed)"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-30",
        "EPD": "126",
        "EventType": "Robbery",
        "EventSubtypes": ["Commercial", "Personal", "Carjacking"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-31",
        "EPD": "130",
        "EventType": "Theft",
        "EventSubtypes": ["Shoplifting"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-32",
        "EPD": "112",
        "EventType": "Medical",
        "EventSubtypes": ["Sudden Death"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-33",
        "EPD": "129",
        "EventType": "Suspicious",
        "EventSubtypes": ["Person"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-33",
        "EPD": "129",
        "EventType": "Suspicious",
        "EventSubtypes": ["Panhandling"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-34",
        "EPD": "130",
        "EventType": "Theft",
        "EventSubtypes": ["Theft"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-35",
        "EPD": "119",
        "EventType": "Harassment/Threats",
        "EventSubtypes": ["Threats", "Stalking"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-36",
        "EPD": "106",
        "EventType": "Sexual Offences",
        "EventSubtypes": ["Sexual Assault"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-37",
        "EPD": "",
        "EventType": "Medical",
        "EventSubtypes": ["Collapse"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-38",
        "EPD": "116",
        "EventType": "Drugs",
        "EventSubtypes": ["Found", "Manufacturing", "Sale", "Use/Possession"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-39",
        "EPD": "113",
        "EventType": "Noise",
        "EventSubtypes": ["Excessive"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-40",
        "EPD": "135",
        "EventType": "Noise",
        "EventSubtypes": ["Possible Gunshots"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-41",
        "EPD": "133",
        "EventType": "Disturbance",
        "EventSubtypes": ["Unwanted Guest"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-42",
        "EPD": "119",
        "EventType": "Harassment/Threats",
        "EventSubtypes": ["Harassment"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-43",
        "EPD": "125",
        "EventType": "Check on Welfare",
        "EventSubtypes": ["Check on welfare"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-43",
        "EPD": "102",
        "EventType": "Check on Welfare",
        "EventSubtypes": ["Abuse", "Neglect", "Abandonment"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-43",
        "EPD": "125",
        "EventType": "Check on Welfare",
        "EventSubtypes": ["Keep the Peace"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-43",
        "EPD": "100-E-1",
        "EventType": "Check on Welfare",
        "EventSubtypes": ["Caller in Imminent Danger"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-43",
        "EPD": "134",
        "EventType": "Check on Welfare",
        "EventSubtypes": ["For Unknown Third Party Events"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-44",
        "EPD": "101",
        "EventType": "Abduction",
        "EventSubtypes": ["Abduction"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-44",
        "EPD": "101",
        "EventType": "Abduction",
        "EventSubtypes": ["Abduction - Parental Family"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-45",
        "EPD": "",
        "EventType": "Assistance",
        "EventSubtypes": ["Notification"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-47",
        "EPD": "101",
        "EventType": "Domestic",
        "EventSubtypes": ["Child Custody"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-53",
        "EPD": "129",
        "EventType": "Suspicious",
        "EventSubtypes": ["Wanted"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-53",
        "EPD": "129",
        "EventType": "Mental Health",
        "EventSubtypes": ["Mental Health Warrant"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-53",
        "EPD": "129",
        "EventType": "Escaped Prisoner",
        "EventSubtypes": ["UAL Warrant"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-69",
        "EPD": "120",
        "EventType": "Suspicious",
        "EventSubtypes": ["Prostitution"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-81",
        "EPD": "132",
        "EventType": "Traffic",
        "EventSubtypes": ["Abandoned Auto"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-82",
        "EPD": "132",
        "EventType": "Traffic",
        "EventSubtypes": ["Careless Driver"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-82",
        "EPD": "132",
        "EventType": "Traffic",
        "EventSubtypes": ["Road Rage"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-83",
        "EPD": "115",
        "EventType": "Traffic",
        "EventSubtypes": ["Drunk Driver"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-84",
        "EPD": "131",
        "EventType": "Accident",
        "EventSubtypes": ["Hit and Run", "Injury/Non-Injury"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-85",
        "EPD": "132",
        "EventType": "Traffic",
        "EventSubtypes": ["Speeder"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-86",
        "EPD": "130",
        "EventType": "Theft",
        "EventSubtypes": ["Stolen Auto - In progress/Late reporting"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-86",
        "EPD": "103",
        "EventType": "Theft",
        "EventSubtypes": ["Stolen Auto - Recovered"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-87",
        "EPD": "129",
        "EventType": "Suspicious",
        "EventSubtypes": ["Vehicle"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-88",
        "EPD": "132",
        "EventType": "Traffic",
        "EventSubtypes": ["Traffic Complaint Misc"],
        "WeaponAvailable": true
    },
    {
        "Code": "10-91",
        "EPD": "",
        "EventType": "Miscellaneous",
        "EventSubtypes": ["Hazardous Good Spill"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-92",
        "EPD": "",
        "EventType": "Miscellaneous",
        "EventSubtypes": ["Incident - Aircraft"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-93",
        "EPD": "",
        "EventType": "Miscellaneous",
        "EventSubtypes": ["Act of Nature"],
        "WeaponAvailable": false
    },
    {
        "Code": "10-97",
        "EPD": "101",
        "EventType": "Suspicious",
        "EventSubtypes": ["Luring"],
        "WeaponAvailable": true
    },
    {
        "Code": "X99",
        "EPD": "122",
        "EventType": "Miscellaneous",
        "EventSubtypes": ["Miscellaneous"],
        "WeaponAvailable": false
    },
    {
        "Code": "100",
        "EPD": "126",
        "EventType": "Major Code",
        "EventSubtypes": ["Bank Hold Up"],
        "WeaponAvailable": true
    },
    {
        "Code": "200",
        "EPD": "124-E-1",
        "EventType": "Major Code",
        "EventSubtypes": ["Code 200 (Officer in Trouble)"],
        "WeaponAvailable": true
    },
    {
        "Code": "300",
        "EPD": "135",
        "EventType": "Major Code",
        "EventSubtypes": ["Firearm Involved in Complaint - Shots Fired (No Victim)"],
        "WeaponAvailable": true
    },
    {
        "Code": "300",
        "EPD": "101",
        "EventType": "Major Code",
        "EventSubtypes": ["Firearm Involved in Complaint - Hostage"],
        "WeaponAvailable": true
    },
    {
        "Code": "300",
        "EPD": "106",
        "EventType": "Major Code",
        "EventSubtypes": ["Firearm Involved in Complaint - Shots Fired (Shooting with Victim)"],
        "WeaponAvailable": true
    },
    {
        "Code": "300",
        "EPD": "136-E-1",
        "EventType": "Active Assailant",
        "EventSubtypes": ["Firearm", "Other Weapon"],
        "WeaponAvailable": true
    },
    {
        "Code": "400",
        "EPD": "109",
        "EventType": "Major Code",
        "EventSubtypes": ["Bomb Threat"],
        "WeaponAvailable": false
    },
    {
        "Code": "400",
        "EPD": "108",
        "EventType": "Major Code",
        "EventSubtypes": ["Found Explosive Object/Package"],
        "WeaponAvailable": false
    },
    {
        "Code": "400",
        "EPD": "117",
        "EventType": "Major Code",
        "EventSubtypes": ["Explosion"],
        "WeaponAvailable": false
    },
    {
        "Code": "500",
        "EPD": "101",
        "EventType": "Major Code",
        "EventSubtypes": ["Extorsion - Hostage Situation"],
        "WeaponAvailable": true
    },
    {
        "Code": "800",
        "EPD": "101",
        "EventType": "Major Code",
        "EventSubtypes": ["Aircraft Hijacking"],
        "WeaponAvailable": true
    },
    {
        "Code": "1000",
        "EPD": "",
        "EventType": "Major Code",
        "EventSubtypes": ["Public Safety (Protest/Marches)"],
        "WeaponAvailable": false
    },
    {
        "Code": "2000",
        "EPD": "",
        "EventType": "Major Code",
        "EventSubtypes": ["Major Incident Response (Large Scale/Natural Disasters)"],
        "WeaponAvailable": false
    },
    {
        "Code": "5000",
        "EPD": "113",
        "EventType": "Major Code",
        "EventSubtypes": ["Prison Uprising/Riot"],
        "WeaponAvailable": true
    },
    {
        "Code": "5000",
        "EPD": "101",
        "EventType": "Major Code",
        "EventSubtypes": ["Prison Uprising/Riot - Condition Blue"],
        "WeaponAvailable": true
    }
]
