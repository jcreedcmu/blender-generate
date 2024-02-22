render:
	./generate_letters.sh
	blender frame.blend --background --python generate.py
