import ctypes
import pyglet
import options

import pyglet.gl as gl

########################Options########################
mipmap_settings = {'SMOOTHING': options.SMOOTHING, 'MIPMAP': options.MIPMAP, 'MIPMAP_TYPE': options.MIPMAP_TYPE}

def get_min_pname(SMOOTHING = False, MIPMAP = False, MIPMAP_TYPE = 'NEAREST'):
	pname = gl.GL_NEAREST
	if SMOOTHING:
		pname = gl.GL_LINEAR
	if MIPMAP:
		if MIPMAP_TYPE == 'NEAREST':
			pname = gl.GL_NEAREST_MIPMAP_NEAREST
			if SMOOTHING:
				pname = gl.GL_LINEAR_MIPMAP_NEAREST

		elif MIPMAP_TYPE == "LINEAR":
			pname = gl.GL_NEAREST_MIPMAP_LINEAR
			if SMOOTHING:
				pname = gl.GL_LINEAR_MIPMAP_LINEAR
	return pname

def get_max_pname(BLUR):
	if BLUR:
		return gl.GL_LINEAR
	return gl.GL_NEAREST
########################Options########################

class Texture_manager:
	def __init__(self, texture_width, texture_height, max_textures):
		self.texture_width = texture_width
		self.texture_height = texture_height

		self.max_textures = max_textures

		self.textures = []

		self.texture_array = gl.GLuint(0)
		gl.glGenTextures(1, self.texture_array)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_array)

		min_pname = get_min_pname(**mipmap_settings)
		max_pname = get_min_pname(options.BLUR)

		gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MIN_FILTER, min_pname)
		gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MAG_FILTER, max_pname)

		gl.glTexImage3D(
			gl.GL_TEXTURE_2D_ARRAY, 0, gl.GL_RGBA,
			self.texture_width, self.texture_height, self.max_textures,
			0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
	
	def generate_mipmaps(self):
		gl.glGenerateMipmap(gl.GL_TEXTURE_2D_ARRAY)
	
	def add_texture(self, texture):
		if not texture in self.textures:
			self.textures.append(texture)

			texture_image = pyglet.image.load(f"textures/{texture}.png").get_image_data()
			gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_array)

			gl.glTexSubImage3D(
				gl.GL_TEXTURE_2D_ARRAY, 0,
				0, 0, self.textures.index(texture),
				self.texture_width, self.texture_height, 1,
				gl.GL_RGBA, gl.GL_UNSIGNED_BYTE,
				texture_image.get_data("RGBA", texture_image.width * 4))