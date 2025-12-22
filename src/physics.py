def get_pit_loss(circuit):
    """
    Returns the average time lost in the pit lane for specific tracks.
    """
    lookup = {
        'Sakhir': 22.5,
        'Bahrain': 22.5,
        'Monza': 24.0,
        'Silverstone': 29.0,
        'Spa-Francorchamps': 21.0,
        'Monaco': 19.0,
    }
    return lookup.get(circuit, 22.0)

def calculate_tyre_cliff_penalty(compound, age):
    penalty = 0.0
    
    # STRICT BAHRAIN LIMITS
    limits = {
        'SOFT': 10,     # Was 12
        'MEDIUM': 18,   # Was 22
        'HARD': 27,     # Was 35 (The 1-Stop Killer)
        'INTERMEDIATE': 30,
        'WET': 30
    }
    
    limit = limits.get(compound.upper(), 30)
    
    if age > limit:
        over_limit = age - limit
        # Severe Penalty: 0.3 * (Over^2)
        penalty = 0.3 * (over_limit ** 2)
        
    return penalty