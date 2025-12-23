def get_race_start_tyres(driver, strategy_mode="Standard Q3"):
    """
    Simulates a race weekend to determine what tyres are left for Sunday.
    Returns a list of available tyre sets with their starting age.
    """
    # 1. BASE INVENTORY (What's left after Practice returns)
    # 1 New Hard, 2 New Mediums, 4 Softs (Indices 3,4,5,6)
    inventory = [
        {'compound': 'HARD', 'age': 0.0, 'status': 'NEW'},
        {'compound': 'MEDIUM', 'age': 0.0, 'status': 'NEW'},
        {'compound': 'MEDIUM', 'age': 0.0, 'status': 'NEW'},
        {'compound': 'SOFT', 'age': 0.0, 'status': 'NEW'},
        {'compound': 'SOFT', 'age': 0.0, 'status': 'NEW'},
        {'compound': 'SOFT', 'age': 0.0, 'status': 'NEW'},
        {'compound': 'SOFT', 'age': 0.0, 'status': 'NEW'},
    ]
    
    # 2. APPLY QUALIFYING DAMAGE
    if strategy_mode == "Standard Q3":
        # Q1 run
        inventory[3]['age'] += 3.0
        inventory[3]['status'] = 'USED'
        # Q2 run
        inventory[4]['age'] += 3.0
        inventory[4]['status'] = 'USED'
        # Q3 runs
        inventory[5]['age'] += 3.0
        inventory[5]['status'] = 'USED'
        inventory[6]['age'] += 3.0
        inventory[6]['status'] = 'USED'
        
    elif strategy_mode == "Knocked out in Q2":
        # Q1 run
        inventory[3]['age'] += 3.0
        inventory[3]['status'] = 'USED'
        # Q2 run
        inventory[4]['age'] += 3.0
        inventory[4]['status'] = 'USED'
        # Inventory 5 & 6 remain NEW (Good for race!)
        
    elif strategy_mode == "Knocked out in Q1":
        # Q1 run (Failed attempt)
        inventory[3]['age'] += 3.0
        inventory[3]['status'] = 'USED'
        # Inventory 4, 5, 6 remain NEW (Great for race!)
        
    return inventory