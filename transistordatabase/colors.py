"""Definitions for different color schemes."""

# matplotlib color specification: https://matplotlib.org/stable/tutorials/colors/colors.html

color_combinations = 255

# The GNOME color scheme fits to the Inkscape integrated GNOME color scheme.
gnome_colors = {"blue": (28 / color_combinations, 113 / color_combinations, 216 / color_combinations),
                'red': (192 / color_combinations, 28 / color_combinations, 40 / color_combinations),
                "green": (46 / color_combinations, 194 / color_combinations, 126 / color_combinations),
                "orange": (230 / color_combinations, 97 / color_combinations, 0 / color_combinations),
                "purple": (129 / color_combinations, 61 / color_combinations, 156 / color_combinations),
                "brown": (134 / color_combinations, 94 / color_combinations, 60 / color_combinations),
                "grey": (119 / color_combinations, 118 / color_combinations, 123 / color_combinations),
                "yellow": (245 / color_combinations, 194 / color_combinations, 17 / color_combinations),
                "black": (0, 0, 0),
                "white": (255 / color_combinations, 255 / color_combinations, 255 / color_combinations)
                }

gnome_colors_list = [gnome_colors["blue"],
                     gnome_colors["red"],
                     gnome_colors["green"],
                     gnome_colors["orange"],
                     gnome_colors["purple"],
                     gnome_colors["brown"],
                     gnome_colors["grey"],
                     gnome_colors["yellow"],
                     gnome_colors["black"]]
