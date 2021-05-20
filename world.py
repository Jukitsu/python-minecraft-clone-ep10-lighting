import math


import chunk

import block_type
import texture_manager
import random

# import custom block models

import models.plant
import models.cactus
import models.cube

light_threads = []

RENDERDISTANCE = 2
WORLDSIZE = 2
max_light_level = models.cube.max_light_level

default_sky_light = 15

class World:
	def __init__(self):
		self.texture_manager = texture_manager.Texture_manager(16, 16, 256)
		self.block_types = [None]

		self.block_types.append(block_type.Block_type(self.texture_manager, "cobblestone", {"all": "cobblestone"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "grass", {"top": "grass", "bottom": "dirt", "sides": "grass_side"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "grass_block", {"all": "grass"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "dirt", {"all": "dirt"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "stone", {"all": "stone"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "sand", {"all": "sand"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "planks", {"all": "planks"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "log", {"top": "log_top", "bottom": "log_top", "sides": "log_side"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "daisy", {"all": "daisy"}, models.plant))
		self.block_types.append(block_type.Block_type(self.texture_manager, "rose", {"all": "rose"}, models.plant))
		self.block_types.append(block_type.Block_type(self.texture_manager, "cactus", {"top": "cactus_top", "bottom": "cactus_bottom", "sides": "cactus_side"}, models.cactus))
		self.block_types.append(block_type.Block_type(self.texture_manager, "dead_bush", {"all": "dead_bush"}, models.plant))
		self.block_types.append(block_type.Block_type(self.texture_manager, "torch", {"all": "torch_on"}, models.plant))
		self.block_types.append(block_type.Block_type(self.texture_manager, "glowstone", {"all": "glowstone"}))

		self.texture_manager.generate_mipmaps()

		self.chunks = {}

		self.lightMap = {}
		self.skylightMap = {}
		# print("Initializing Light Map")

		for x in range(RENDERDISTANCE):
			for z in range(RENDERDISTANCE):
				chunk_position = (x - 1, -1, z - 1)
				current_chunk = chunk.Chunk(self, chunk_position)

				for i in range(chunk.CHUNK_WIDTH):
					for j in range(chunk.CHUNK_HEIGHT):
						for k in range(chunk.CHUNK_LENGTH):
							if j == 13: current_chunk.blocks[i][j][k] = random.choices([0, 9, 10], [20, 2, 1])[0]
							elif j == 12: current_chunk.blocks[i][j][k] = 2
							elif 9 < j < 12: current_chunk.blocks[i][j][k] = 4
							elif j < 10: current_chunk.blocks[i][j][k] = 5
				self.chunks[chunk_position] = current_chunk

		for x in range(RENDERDISTANCE * chunk.CHUNK_WIDTH):
			for z in range(RENDERDISTANCE * chunk.CHUNK_LENGTH):
				x1 = x - RENDERDISTANCE * chunk.CHUNK_WIDTH / 2
				z1 = z - RENDERDISTANCE * chunk.CHUNK_LENGTH / 2
				pos = (x1, 0, z1)
				self.init_skylight(*pos, default_sky_light)

		for chunk_position in self.chunks:
			self.chunks[chunk_position].update_subchunk_meshes()
			self.chunks[chunk_position].update_mesh()

	def getfacelight(self, x, y, z, face_number):
		face = self.get_direction_vector(face_number)
		skylight = self.get_sky_light(x+face[0], y+face[1], z+face[2])
		if skylight < 0:
			skylight = default_sky_light/2
		return max(self.get_block_light(x+face[0], y+face[1], z+face[2]), skylight)

	def init_skylight(self, x, y, z, light, ignore=[]):
		print(f"creating skylight at {x} {y} {z}")
		if self.is_opaque_block((x, y, z)):
			return
		self.set_sky_light(x, y, z, light)
		if (x, y, z) in ignore:
			return
		if abs(x) > chunk.CHUNK_WIDTH * RENDERDISTANCE or y < -16 or y > 16 or abs(
				z) > chunk.CHUNK_LENGTH * RENDERDISTANCE:
			return
		if not light:
			return
		vector = self.get_direction_vector(3)
		pos = (x + vector[0], y + vector[1], z + vector[2])
		l = light + 1
		if self.is_opaque_block(pos) or pos in ignore or self.get_sky_light(*pos) >= l:
			return
		ignore += [(x, y, z)]
		self.init_skylight(*pos, l - 1, ignore)

	def create_skylight(self, x, y, z, light, ignore=[]):  # Currently Broken
		print(f"creating skylight at {x} {y} {z}")
		if self.is_opaque_block((x, y, z)):
			return
		self.set_sky_light(x, y, z, light)
		if (x, y, z) in ignore:
			return
		if abs(x) > chunk.CHUNK_WIDTH * RENDERDISTANCE or y < -16 or y > 16 or abs(z) > chunk.CHUNK_LENGTH * RENDERDISTANCE:
			return
		if not light:
			return
		for face in range(0, 6):
			vector = self.get_direction_vector(face)
			pos = (x + vector[0], y + vector[1], z + vector[2])
			l = light
			if face == 3:
				l = light + 1
			if self.is_opaque_block(pos) or pos in ignore or self.get_sky_light(*pos) >= l:
				continue
			ignore += [(x, y, z)]
			self.create_skylight(*pos, l - 1, ignore)

	def remove_skylight(self, x, y, z, ignore=[]):
		if self.is_opaque_block((x, y, z)):
			self.set_sky_light(x, y, z, 0)
			return
		self.set_sky_light(x, y, z, 0)
		if (x, y, z) in ignore:
			return
		if abs(x) > chunk.CHUNK_WIDTH * RENDERDISTANCE or y < -16 or y > 16 or abs(z) > chunk.CHUNK_LENGTH * RENDERDISTANCE:
			return
		for face in range(0, 6):
			vector = self.get_direction_vector(face)
			pos = (x + vector[0], y + vector[1], z + vector[2])
			l = 0
			if self.is_opaque_block(pos) or pos in ignore or self.get_sky_light(*pos) >= l:
				continue
			ignore += [(x, y, z)]
			self.remove_skylight(*pos, l - 1, ignore)

	def create_light(self, x, y, z, l, ignore=None):
		if self.is_opaque_block((x, y, z)) or self.get_block_light(x, y, z) >= l:
			return
		self.set_block_light(x, y, z, l)
		if ignore == (x, y, z): #ignore already updated light
			return
		if not l:
			return
		for face in range(0, 6):
			vector = self.get_direction_vector(face)
			pos = (x + vector[0], y + vector[1], z + vector[2])
			if self.is_opaque_block(pos) or ignore == pos or self.get_block_light(*pos) > l:
				continue
			self.create_light(*pos, l - 1, (x, y, z))

	def remove_light(self, x, y, z, ignore=None):
		l = self.get_block_light(x, y, z)
		if not l:
			return
		self.set_block_light(x, y, z, 0)
		if ignore == (x, y, z): #ignore already updated light
			return
		for face in range(0, 6):
			vector = self.get_direction_vector(face)
			pos = (x + vector[0], y + vector[1], z + vector[2])
			if self.is_opaque_block(pos) or ignore == pos or self.get_block_light(*pos) > l:
				continue
			self.remove_light(*pos, (x, y, z))

	def get_direction_vector(self, face_number):
		face = ()
		if face_number == 0:  # EAST
			face = (1, 0, 0)
		if face_number == 1:  # WEST
			face = (-1, 0, 0)
		if face_number == 2:
			face = (0, 1, 0)  # UP
		if face_number == 3:
			face = (0, -1, 0)  # DOWN
		if face_number == 4:
			face = (0, 0, 1)  # SOUTH
		if face_number == 5:
			face = (0, 0, -1) # NORTH
		return face

	def get_sky_light(self, x, y, z):
		return self.skylightMap.get((x, y, z), -1)

	def set_sky_light(self, x, y, z, light):
		self.skylightMap[(x, y, z)] = light

	def get_block_light(self, x, y, z):
		return self.lightMap.get((x, y, z), 0)

	def set_block_light(self, x, y, z, light):
		self.lightMap[(x, y, z)] = light

	def update_skylight(self, chunkposition):
		_chunk = self.chunks.get(chunkposition, None)
		if _chunk is None:
			return
		for lx in range(chunk.CHUNK_WIDTH):
			for ly in range(chunk.CHUNK_HEIGHT):
				for lz in range(chunk.CHUNK_LENGTH):
					x = lx + chunk.CHUNK_WIDTH * chunkposition[0]
					y = lx + chunk.CHUNK_HEIGHT * chunkposition[1]
					z = lx + chunk.CHUNK_LENGTH * chunkposition[2]
					self.set_sky_light(x, y, z, 0)
		for lx in range(chunk.CHUNK_WIDTH):
			for lz in range(chunk.CHUNK_LENGTH):
				x = lx + chunk.CHUNK_WIDTH * chunkposition[0]
				z = lx + chunk.CHUNK_LENGTH * chunkposition[2]
				self.create_light(x, 0, z, default_sky_light)



	# create functions to make things a bit easier

	def get_chunk_position(self, position):
		x, y, z = position

		return (
			math.floor(x / chunk.CHUNK_WIDTH),
			math.floor(y / chunk.CHUNK_HEIGHT),
			math.floor(z / chunk.CHUNK_LENGTH))

	def get_local_position(self, position):
		x, y, z = position

		return (
			int(x % chunk.CHUNK_WIDTH),
			int(y % chunk.CHUNK_HEIGHT),
			int(z % chunk.CHUNK_LENGTH))

	def get_block_number(self, position):
		x, y, z = position
		chunk_position = self.get_chunk_position(position)

		if not chunk_position in self.chunks:
			return 0

		lx, ly, lz = self.get_local_position(position)

		block_number = self.chunks[chunk_position].blocks[lx][ly][lz]
		return block_number

	def is_opaque_block(self, position):
		# get block type and check if it's opaque or not
		# air counts as a transparent block, so test for that too

		block_type = self.block_types[self.get_block_number(position)]

		if not block_type:
			return False

		return not block_type.transparent

	def set_block(self, position, number): # set number to 0 (air) to remove block
		x, y, z = position
		chunk_position = self.get_chunk_position(position)




		if not chunk_position in self.chunks: # if no chunks exist at this position, create a new one
			if number == 0:
				return # no point in creating a whole new chunk if we're not gonna be adding anything

			self.chunks[chunk_position] = chunk.Chunk(self, chunk_position)

		if self.get_block_number(position) == number: # no point updating mesh if the block is the same
			return

		if not number and (self.get_block_number(position) == 13 or self.get_block_number(position) == 14):
			self.remove_light(x, y, z)


		if number == 13 or number == 14:
			self.create_light(x, y, z, 14)

		lx, ly, lz = self.get_local_position(position)



		self.chunks[chunk_position].blocks[lx][ly][lz] = number


		if number:
			self.update_skylight(chunk_position)

		if not number and not (self.get_block_number(position) == 13 or number == 14):
			lights = []
			slights = []
			for f in range(0, 6):
				face = self.get_direction_vector(f)
				lights.append(self.get_block_light(x+face[0], y+face[1], z+face[2]))
				slights.append(self.get_sky_light(x + face[0], y + face[1], z + face[2]))
			l = max(lights)
			sl = max(slights)
			self.create_skylight(x, y, z, sl - 1)
			self.create_light(x, y, z, l-1)

		if number:
			if self.is_opaque_block(position):
				self.set_sky_light(*position, 0)
				self.set_block_light(*position, 0)

		self.chunks[chunk_position].update_at_position((x, y, z))
		self.chunks[chunk_position].update_mesh()

		cx, cy, cz = chunk_position

		def try_update_chunk_at_position(chunk_position, position):
			if chunk_position in self.chunks:
				self.chunks[chunk_position].update_at_position(position)
				self.chunks[chunk_position].update_mesh()

		if lx == chunk.CHUNK_WIDTH - 1: try_update_chunk_at_position((cx + 1, cy, cz), (x + 1, y, z))
		if lx == 0: try_update_chunk_at_position((cx - 1, cy, cz), (x - 1, y, z))

		if ly == chunk.CHUNK_HEIGHT - 1: try_update_chunk_at_position((cx, cy + 1, cz), (x, y + 1, z))
		if ly == 0: try_update_chunk_at_position((cx, cy - 1, cz), (x, y - 1, z))

		if lz == chunk.CHUNK_LENGTH - 1: try_update_chunk_at_position((cx, cy, cz + 1), (x, y, z + 1))
		if lz == 0: try_update_chunk_at_position((cx, cy, cz - 1), (x, y, z - 1))

	def draw(self):
		for chunk_position in self.chunks:
			self.chunks[chunk_position].draw()
