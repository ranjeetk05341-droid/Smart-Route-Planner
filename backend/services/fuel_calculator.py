class FuelCalculator:
    # Baseline fuel/energy efficiency (km per unit: Liters for gas/diesel, kWh for EV)
    DEFAULT_EFFICIENCY = {
        'petrol': 15.0,    # km / Liter
        'diesel': 13.0,    # km / Liter
        'ev': 6.5,         # km / kWh
        'hybrid': 22.0,    # km / Liter
        'bike': 45.0,      # km / Liter
        'truck': 5.5       # km / Liter
    }

    # Baseline default fuel/energy cost per unit
    DEFAULT_UNIT_PRICE = {
        'petrol': 1.45,    # $ / Liter (or local currency unit)
        'diesel': 1.35,
        'ev': 0.22,        # $ / kWh
        'hybrid': 1.45,
        'bike': 1.45,
        'truck': 1.35
    }

    # Average CO2 emission in grams per unit (Liter or kWh)
    CO2_GRAMS_PER_UNIT = {
        'petrol': 2392.0,  # ~2.39 kg CO2 per liter petrol
        'diesel': 2640.0,  # ~2.64 kg CO2 per liter diesel
        'ev': 450.0,       # ~0.45 kg CO2 per kWh (grid average)
        'hybrid': 1600.0,
        'bike': 800.0,
        'truck': 2800.0
    }

    @classmethod
    def calculate(cls, distance_km, vehicle_type='petrol', user_fuel_price=None, user_efficiency=None, traffic_multiplier=1.0):
        vehicle = vehicle_type.lower() if vehicle_type else 'petrol'
        if vehicle not in cls.DEFAULT_EFFICIENCY:
            vehicle = 'petrol'

        # Efficiency in km / unit
        efficiency = user_efficiency if (user_efficiency and user_efficiency > 0) else cls.DEFAULT_EFFICIENCY[vehicle]
        
        # Unit price
        unit_price = user_fuel_price if (user_fuel_price and user_fuel_price > 0) else cls.DEFAULT_UNIT_PRICE[vehicle]

        # In heavy traffic, engine idling and start-stop cycles increase consumption
        traffic_penalty = 1.0 + max(0.0, (traffic_multiplier - 1.0) * 0.35)

        units_consumed = (distance_km / efficiency) * traffic_penalty
        total_cost = units_consumed * unit_price
        co2_emissions_kg = (units_consumed * cls.CO2_GRAMS_PER_UNIT.get(vehicle, 2392.0)) / 1000.0

        return {
            'vehicle_type': vehicle,
            'efficiency_km_per_unit': round(efficiency, 1),
            'unit_price': round(unit_price, 2),
            'units_consumed': round(units_consumed, 2),
            'unit_label': 'kWh' if vehicle == 'ev' else 'L',
            'fuel_cost': round(total_cost, 2),
            'co2_emissions_kg': round(co2_emissions_kg, 2),
            'traffic_penalty_factor': round(traffic_penalty, 2)
        }

