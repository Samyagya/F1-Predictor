def get_pit_loss(circuit):
    """
    Returns the estimated time lost in the pit lane for all 2025 circuits.
    Includes Pit Entry, Speed Limit, and Pit Exit delta.
    """
    # Map common names to 2025 Calendar Standard
    lookup = {
        # --- HIGH PIT LOSS (>24s) ---
        'Silverstone': 29.0,
        'Singapore': 28.5,
        'Imola': 28.0,
        'Paul Ricard': 27.0,
        'Lusail': 26.0,    # Qatar
        'Suzuka': 25.0,
        
        # --- MEDIUM PIT LOSS (22-24s) ---
        'Bahrain': 22.5,
        'Sakhir': 22.5,
        'Shanghai': 24.0,  # China
        'Miami': 23.0,
        'Barcelona': 23.5, # Spain
        'Las Vegas': 23.0,
        'Yas Marina': 23.0, # Abu Dhabi
        'Albert Park': 22.5, # Australia
        'Mexico City': 22.5,
        'Hungaroring': 22.0,
        'Zandvoort': 22.0,
        'Jeddah': 21.5,
        
        # --- LOW PIT LOSS (<21s) ---
        'Spa': 21.0,       # Belgium
        'Spa-Francorchamps': 21.0,
        'Red Bull Ring': 20.5, # Austria
        'Monza': 24.0,     # High speed entry, but long lane. Actually ~24s total impact
        'Interlagos': 20.5, # Brazil
        'Baku': 21.0,      # Azerbaijan
        'Montreal': 19.5,  # Canada (Short pit lane)
        'Monaco': 19.0     # Super short
    }
    
    # Default to 22.5s (Average) if track is unknown
    return lookup.get(circuit, 22.5)

def calculate_tyre_cliff_penalty(compound, age):
    """
    Calculates tyre degradation penalty with 'Cliff' logic.
    """
    penalty = 0.0
    
    # 2025-Spec Tyre Limits (Approximate)
    limits = {
        'SOFT': 12,
        'MEDIUM': 20,
        'HARD': 32,
        'INTERMEDIATE': 25,
        'WET': 25
    }
    
    limit = limits.get(compound.upper(), 25)
    
    if age > limit:
        over_limit = age - limit
        # Penalty grows exponentially: 0.3s * (Over^2)
        # 1 lap over = +0.3s
        # 5 laps over = +7.5s
        penalty = 0.3 * (over_limit ** 2)
        
    return penalty