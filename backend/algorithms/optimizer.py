def get_mode_weights(mode):
    """
    Returns the normalized weights for the selected optimization mode.
    Modes: 'fastest', 'shortest', 'economical', 'balanced'
    """
    weights_map = {
        'fastest': {
            'time_weight': 0.65,
            'dist_weight': 0.15,
            'cost_weight': 0.10,
            'traffic_weight': 0.10,
            'description': 'Prioritizes minimizing total travel duration and bypassing congestion.'
        },
        'shortest': {
            'time_weight': 0.15,
            'dist_weight': 0.70,
            'cost_weight': 0.15,
            'traffic_weight': 0.00,
            'description': 'Prioritizes minimal physical road kilometers.'
        },
        'economical': {
            'time_weight': 0.15,
            'dist_weight': 0.20,
            'cost_weight': 0.65,
            'traffic_weight': 0.00,
            'description': 'Prioritizes lowest fuel/energy consumption and toll expenses.'
        },
        'balanced': {
            'time_weight': 0.35,
            'dist_weight': 0.30,
            'cost_weight': 0.25,
            'traffic_weight': 0.10,
            'description': 'Optimal multi-criteria compromise between time, distance, and fuel cost.'
        }
    }
    return weights_map.get(mode.lower(), weights_map['balanced'])


def evaluate_and_rank_routes(routes, mode='balanced', custom_weights=None):
    """
    Evaluates candidate routes using Multi-Objective Weighted Normalization.
    
    Formula:
      Score = (w_d * D_norm) + (w_t * T_norm) + (w_c * C_norm) + (w_trf * Trf_norm)
      Where all normalized values are in [0.0, 1.0].
      Lower score = better route.
      Efficiency Score (0 - 100%) = 100 * (1 - (Score - min_score) / max_diff) or absolute scaled.
    """
    if not routes:
        return []

    # Get weight dictionary
    if custom_weights:
        weights = custom_weights
    else:
        weights = get_mode_weights(mode)

    w_d = weights.get('dist_weight', 0.30)
    w_t = weights.get('time_weight', 0.35)
    w_c = weights.get('cost_weight', 0.25)
    w_trf = weights.get('traffic_weight', 0.10)

    # Normalize weights so sum equals 1.0
    total_w = w_d + w_t + w_c + w_trf
    if total_w > 0:
        w_d /= total_w
        w_t /= total_w
        w_c /= total_w
        w_trf /= total_w

    # Find max values for normalization (avoid zero division)
    max_dist = max((r.get('distance_km', 1.0) for r in routes), default=1.0) or 1.0
    max_time = max((r.get('duration_min', 1.0) for r in routes), default=1.0) or 1.0
    max_cost = max((r.get('fuel_cost', 1.0) for r in routes), default=1.0) or 1.0
    max_trf = max((r.get('traffic_multiplier', 1.0) for r in routes), default=1.0) or 1.0

    scored_routes = []
    for r in routes:
        route_copy = dict(r)

        # Check for road closures
        has_closure = route_copy.get('has_road_closure', False)
        if has_closure:
            route_copy['composite_score'] = 9999.0
            route_copy['efficiency_score'] = 0.0
            route_copy['is_blocked'] = True
            route_copy['badge'] = 'Blocked by Closure'
            scored_routes.append(route_copy)
            continue

        d_norm = route_copy.get('distance_km', 0.0) / max_dist
        t_norm = route_copy.get('duration_min', 0.0) / max_time
        c_norm = route_copy.get('fuel_cost', 0.0) / max_cost
        trf_norm = (route_copy.get('traffic_multiplier', 1.0) - 1.0) / (max(max_trf - 1.0, 0.01))

        composite_score = (w_d * d_norm) + (w_t * t_norm) + (w_c * c_norm) + (w_trf * trf_norm)
        route_copy['composite_score'] = round(composite_score, 4)
        route_copy['is_blocked'] = False
        scored_routes.append(route_copy)

    # Sort routes by composite score ascending (lowest score is best)
    scored_routes.sort(key=lambda x: x['composite_score'])

    # Determine relative efficiency score (0 - 100) and badges
    valid_routes = [r for r in scored_routes if not r.get('is_blocked', False)]
    if valid_routes:
        best_score = valid_routes[0]['composite_score']
        worst_score = valid_routes[-1]['composite_score']
        score_range = max(worst_score - best_score, 0.05)

        for i, r in enumerate(valid_routes):
            # Scale relative to best: 100 for best, decrementing based on distance from best
            relative_drop = (r['composite_score'] - best_score) / score_range
            efficiency = max(50.0, round(100.0 - (relative_drop * 40.0), 1))
            r['efficiency_score'] = efficiency

            # Assign badges
            if i == 0:
                if mode == 'fastest':
                    r['badge'] = 'Fastest Route'
                elif mode == 'shortest':
                    r['badge'] = 'Shortest Distance'
                elif mode == 'economical':
                    r['badge'] = 'Most Economical'
                else:
                    r['badge'] = 'Recommended Best'
                r['is_recommended'] = True
            else:
                r['is_recommended'] = False
                if r.get('distance_km') == min(x['distance_km'] for x in valid_routes):
                    r['badge'] = 'Shortest Alternative'
                elif r.get('duration_min') == min(x['duration_min'] for x in valid_routes):
                    r['badge'] = 'Quick Alternative'
                elif r.get('fuel_cost') == min(x['fuel_cost'] for x in valid_routes):
                    r['badge'] = 'Economy Alternative'
                else:
                    r['badge'] = f'Alternative {i}'

    return scored_routes

