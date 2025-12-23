def get_pit_loss(circuit):
    """
    Returns the estimated time lost in the pit lane for the 2026 Calendar.
    Data includes new tracks like Madrid.
    """
    lookup = {
        # --- HIGH PIT LOSS (>24s) ---
        'Silverstone': 29.0,
        'Singapore': 28.5,
        'Paul Ricard': 27.0,
        'Lusail': 26.0,    # Qatar
        'Suzuka': 25.0,
        
        # --- MEDIUM PIT LOSS (22-24s) ---
        'Bahrain': 22.5,
        'Sakhir': 22.5,
        'Shanghai': 24.0,  # China
        'Miami': 23.0,
        'Barcelona': 23.0, # Spanish GP (Catalunya)
        'Madrid': 23.5,    # NEW: Madrid Street Circuit (Est. similar to Valencia/Baku)
        'Las Vegas': 23.0,
        'Yas Marina': 23.0, # Abu Dhabi
        'Albert Park': 22.5, # Australia
        'Mexico City': 22.5,
        'Hungaroring': 22.0,
        'Zandvoort': 22.0,
        'Jeddah': 21.5,
        'Austin': 22.5,    # COTA
        
        # --- LOW PIT LOSS (<21s) ---
        'Spa': 21.0,
        'Red Bull Ring': 20.5, # Austria
        'Monza': 24.0,     # High speed entry impacts total delta
        'Interlagos': 20.5, # Brazil
        'Baku': 21.0,      # Azerbaijan
        'Montreal': 19.5,  # Canada
        'Monaco': 19.0     # Shortest lane
    }
    
    # Default to 22.5s if unknown
    return lookup.get(circuit, 22.5)

def calculate_tyre_cliff_penalty(compound, age):
    penalty = 0.0
    
    # AGGRESSIVE BAHRAIN DEGRADATION
    limits = {
        'SOFT': 15,      # Fast but short life
        'MEDIUM': 20,    # Good for 20 laps
        'HARD': 25,      # NERFED: Was 35. Now dies at 25.
        'INTERMEDIATE': 28,
        'WET': 28
    }
    
    limit = limits.get(compound.upper(), 25)
    
    if age > limit:
        over_limit = age - limit
        # The "Cliff" is steep: 0.35s per lap squared
        penalty = 0.35 * (over_limit ** 2)
        
    return penalty