transparent = True
is_cube = False
import options

vertex_positions = [
    [-0.3536, 0.5000, 0.3536, -0.3536, -0.5000, 0.3536, 0.3536, -0.5000, -0.3536, 0.3536, 0.5000, -0.3536],
    [-0.3536, 0.5000, -0.3536, -0.3536, -0.5000, -0.3536, 0.3536, -0.5000, 0.3536, 0.3536, 0.5000, 0.3536],
    [0.3536, 0.5000, -0.3536, 0.3536, -0.5000, -0.3536, -0.3536, -0.5000, 0.3536, -0.3536, 0.5000, 0.3536],
    [0.3536, 0.5000, 0.3536, 0.3536, -0.5000, 0.3536, -0.3536, -0.5000, -0.3536, -0.3536, 0.5000, -0.3536],
]

tex_coords = [
    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0],
]

shading_values = [
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
]

max_light_level = 15


def get_face_shading_values(light_level, face_number):
    if not options.LIGHTING:
        return shading_values[face_number]
    light_multiplier = 1
    if options.LIGHTING_TYPE == "EXPONENTIAL":
        light_multiplier = min(0.8 ** (max_light_level - light_level) + options.BRIGHTNESS / 5, 1)
    elif options.LIGHTING_TYPE == "LINEAR":
        light_multiplier = (light_level + 1 + options.BRIGHTNESS * 2) / (max_light_level + 1)
    s = (shading_values[face_number][0] * light_multiplier)
    t = [s, s, s, s]
    return t
