"""
optimizer.py
------------
Route optimization engine for the Delivery Route Optimizer project.

Given a depot (start point) and a list of delivery stops (lat/lng pairs),
this module computes:
  1. A haversine-based distance matrix (no external map API needed).
  2. An initial route using the Nearest Neighbor heuristic.
  3. An improved route using 2-opt local search.

This mirrors the real logistics problem Amazon HackOn poses: given N
delivery addresses, find a route that minimizes total travel distance
for a delivery agent, without needing a paid routing API.
"""

import math
from itertools import combinations


def haversine(coord1, coord2):
    """Great-circle distance in kilometers between two (lat, lng) points."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371.0  # Earth radius in km

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def build_distance_matrix(points):
    """points: list of (lat, lng) tuples, index 0 = depot."""
    n = len(points)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(points[i], points[j])
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix


def route_distance(route, matrix):
    return sum(matrix[route[i]][route[i + 1]] for i in range(len(route) - 1))


def nearest_neighbor(matrix, start=0):
    """Greedy construction heuristic: always go to the closest unvisited stop."""
    n = len(matrix)
    unvisited = set(range(n)) - {start}
    route = [start]
    current = start
    while unvisited:
        nxt = min(unvisited, key=lambda j: matrix[current][j])
        route.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    return route


def two_opt(route, matrix, max_passes=100):
    """
    Local search improvement: repeatedly reverse segments of the route
    if doing so shortens total distance, until no improvement is found
    (or max_passes reached). Classic 2-opt for TSP-style routing.
    """
    best = route[:]
    improved = True
    passes = 0

    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                if j - i == 1:
                    continue
                a, b, c, d = best[i - 1], best[i], best[j], best[j + 1]
                current_cost = matrix[a][b] + matrix[c][d]
                new_cost = matrix[a][c] + matrix[b][d]
                if new_cost < current_cost - 1e-9:
                    best[i:j + 1] = best[i:j + 1][::-1]
                    improved = True
    return best


def optimize_route(points):
    """
    points: list of dicts [{"lat":..., "lng":..., "label":...}, ...]
            index 0 is treated as the depot / warehouse.

    Returns a dict with the naive order, NN route, 2-opt route, and
    distances for each, so the frontend can show the before/after gain.
    """
    coords = [(p["lat"], p["lng"]) for p in points]
    matrix = build_distance_matrix(coords)
    n = len(coords)

    naive_route = list(range(n))  # visit in the order they were entered
    nn_route = nearest_neighbor(matrix, start=0)
    optimized_route = two_opt(nn_route, matrix)

    def to_output(route):
        return {
            "order": route,
            "labels": [points[i].get("label", f"Stop {i}") for i in route],
            "distance_km": round(route_distance(route, matrix), 3),
        }

    naive = to_output(naive_route)
    nn = to_output(nn_route)
    opt = to_output(optimized_route)

    saved_km = round(naive["distance_km"] - opt["distance_km"], 3)
    saved_pct = round((saved_km / naive["distance_km"]) * 100, 1) if naive["distance_km"] > 0 else 0.0

    return {
        "naive": naive,
        "nearest_neighbor": nn,
        "optimized": opt,
        "distance_saved_km": saved_km,
        "distance_saved_pct": saved_pct,
    }


if __name__ == "__main__":
    # Quick manual smoke test
    demo_points = [
        {"lat": 30.9010, "lng": 75.8573, "label": "Warehouse (Ludhiana)"},
        {"lat": 30.9100, "lng": 75.8200, "label": "Customer A"},
        {"lat": 30.8800, "lng": 75.8700, "label": "Customer B"},
        {"lat": 30.9250, "lng": 75.8400, "label": "Customer C"},
        {"lat": 30.8950, "lng": 75.7900, "label": "Customer D"},
    ]
    result = optimize_route(demo_points)
    import json
    print(json.dumps(result, indent=2))
