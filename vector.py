import math

class Vec3D:
    def __init__(self, *args):
        if len(args) == 1:
            self.vector = args[0]
            self.x, self.y, self.z = args[0]
        elif len(args) == 3:
            x, y, z = args
            self.x = x
            self.y = y
            self.z = z
            self.vector = (x, y, z)

    def __add__(self, obj):
        return Vec3D(self.x + obj.x, self.y + obj.y, self.z + obj.z)

    def __mul__(self, obj):
        if isinstance(obj, Vec3D):
            return self.x * obj.x + self.y * obj.y + self.z * obj.z
        else:
            raise TypeError

    def __rmul__(self, obj):
        if isinstance(obj, Vec3D):
            return self.x * obj.x + self.y * obj.y + self.z * obj.z
        else:
            return Vec3D(self.x * obj, self.y * obj, self.z * obj)

    def __pow__(self, vec):
        if isinstance(vec, Vec3D):
            return Vec3D(self.y*vec.z - self.z*vec.y, self.z*vec.x - self.x*vec.z, self.x*vec.y - self.y*self.x)
        else:
            return self.x**vec+self.y**vec+self.z**vec

    def __repr__(self):
        return f"Vec3D({self.x}, {self.y}, {self.z})"

    def __abs__(self):
        return math.sqrt(self**2)

    def __xor__(self, obj):
        return math.acos(self*obj/(abs(self)*abs(obj)))

    def __iter__(self):
        return iter(self.vector)

    def __getitem__(self, index):
        return self.vector[index]


NORTH = Vec3D(0, 0, -1)
SOUTH = Vec3D(0, 0, 1)
WEST = Vec3D(-1, 0, 0)
EAST = Vec3D(1, 0, 0)
UP = Vec3D(0, 1, 0)
DOWN = Vec3D(0, -1, 0)

