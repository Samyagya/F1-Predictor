from datetime import datetime

# 2026 Provisional Calendar (Dates are hypothetical/estimated for the project)
RACE_CALENDAR = [
    {"round": 1, "circuit": "Sakhir", "date": "2026-03-01"},
    {"round": 2, "circuit": "Jeddah", "date": "2026-03-08"},
    {"round": 3, "circuit": "Albert Park", "date": "2026-03-22"},
    {"round": 4, "circuit": "Suzuka", "date": "2026-04-05"},
    {"round": 5, "circuit": "Shanghai", "date": "2026-04-19"},
    {"round": 6, "circuit": "Miami", "date": "2026-05-03"},
    {"round": 7, "circuit": "Imola", "date": "2026-05-17"},
    {"round": 8, "circuit": "Monaco", "date": "2026-05-24"},
    {"round": 9, "circuit": "Montreal", "date": "2026-06-07"},
    {"round": 10, "circuit": "Barcelona", "date": "2026-06-21"},
    {"round": 11, "circuit": "Red Bull Ring", "date": "2026-06-28"},
    {"round": 12, "circuit": "Silverstone", "date": "2026-07-05"},
    {"round": 13, "circuit": "Hungaroring", "date": "2026-07-19"},
    {"round": 14, "circuit": "Spa", "date": "2026-07-26"},
    {"round": 15, "circuit": "Zandvoort", "date": "2026-08-30"},
    {"round": 16, "circuit": "Monza", "date": "2026-09-06"},
    {"round": 17, "circuit": "Baku", "date": "2026-09-20"},
    {"round": 18, "circuit": "Singapore", "date": "2026-10-04"},
    {"round": 19, "circuit": "Austin", "date": "2026-10-18"},
    {"round": 20, "circuit": "Mexico City", "date": "2026-10-25"},
    {"round": 21, "circuit": "Interlagos", "date": "2026-11-08"},
    {"round": 22, "circuit": "Las Vegas", "date": "2026-11-21"},
    {"round": 23, "circuit": "Lusail", "date": "2026-11-29"},
    {"round": 24, "circuit": "Yas Marina", "date": "2026-12-06"}
]

def get_next_race():
    """
    Finds the next race based on the current date.
    If the season is over (or hasn't started), it loops or defaults.
    """
    now = datetime.now()
    # For simulation, let's pretend 'now' is in 2026 if we are testing
    # Or we just map current Month/Day to 2026
    current_date_str = f"2026-{now.month:02d}-{now.day:02d}"
    
    for race in RACE_CALENDAR:
        if race['date'] >= current_date_str:
            return race
            
    return RACE_CALENDAR[0] # Default to Round 1 if season over