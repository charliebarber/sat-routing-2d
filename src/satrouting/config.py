"""Configuration constants for the routing system."""

# Ground station configurations
GROUND_STATIONS = [-1, -2]  # LDN and NYC
GROUND_STATION_POSITIONS = {
    -1: (38.5, -5.5),  # LDN
    -2: (25, -6.5),    # NYC
}

# Spare zone configurations
SPARE_ZONES = [(269, 328, 334, 393), (467, 522, 532, 587)]

# Network parameters
SATS_PER_PLANE = 66
DISPLAY_BOUNDS = {
    'x_min': 26,
    'x_max': 40,
    'y_min': -8,
    'y_max': -4,
}

# Routing parameters
TARGET_WEIGHT_FACTOR = 1.25  # 25% above shortest path