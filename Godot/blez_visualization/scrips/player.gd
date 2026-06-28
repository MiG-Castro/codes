extends CharacterBody3D
@onready var camera_mount = $camera_mount
@onready var skel  = $visuals/mixamo_base/Armature/Skeleton3D
@onready var animation_player = $visuals/mixamo_base/AnimationPlayer
@onready var visuals = $visuals
@export var sens_horizontal = 0.5
@export var sens_vertical = 0.5

var unlock_mouse = false  
 
# socket UDP
var server := UDPServer.new()
var port = 4000
var peers = []
var buffer = StreamPeerBuffer.new()
var no_pkt = 0

var SPEED = 3.0
const JUMP_VELOCITY = 4.5
const walking_speed = 3.0

var pres_sit = false
var reset_q = false
var inv_qua = Quaternion()


# Ajuste de cuaternion del sensor para que coincidan los ejes
var empy = false
var s = 0 # Sensor Node ID
var q_mod = [1,-1,-1,1] 
var rot_quat_0 = Quaternion() # x, y, z, w # Rx quat
var rot_quat_1 = Quaternion() # x, y, z, w # quat of the previus bone
var rot_quat_2 = Quaternion() # x, y, z, w # Final quat

# Rotaciones de referencia
var identidad = Quaternion(0,0,0,1) # Equivalente a multiplicar por 1
var horizontal = Quaternion(0.70711, 0.00000, 0.00000, 0.70711) 

# Quaterniones para ajustar a posicion especifica
var QInv_0 = identidad
var QInv_1 = identidad
var QInv_2 = identidad

var w = 0.0
var x = 0.0
var y = 0.0
var z = 0.0

var w0 = 0
var x0 = 0
var y0 = 0
var z0 = 0

# Get the gravity from the project settings to be synced with RigidBody nodes.
var gravity = ProjectSettings.get_setting("physics/3d/default_gravity")
var hueso = 0
var id = [0, 0, 0, 0, 0, 0]

var pks_x_s = 0
var Rx_pkts = 0
var count_frames = 0
var time_now = Time.get_time_string_from_system()

func _ready():
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	id[0] = skel.find_bone("mixamorig_RightArm")
	id[1] = skel.find_bone("mixamorig_RightForeArm")
	id[2] = skel.find_bone("mixamorig_RightHand")
	
	id[3] = skel.find_bone("mixamorig_LeftArm")
	id[4] = skel.find_bone("mixamorig_LeftForeArm")
	id[5] = skel.find_bone("mixamorig_LeftHand")
	
	# skel.find_bone("mixamorig_RightLeg")
	
	for k in id:
		skel.set_bone_pose_rotation(k, identidad)
	
	set_process(true)
	
	# Intentar conectar el socket al puerto en localhost
	var result = server.listen(port)
	if result != OK:
		print("Error al iniciar el servidor UDP: ", result)
	else:
		print("Servidor UDP iniciado en el puerto ", port)
	
func _input(event):
	if event is InputEventMouseMotion:
		if not unlock_mouse:
			# Rotacion del eje Y del MODELO con mouse (cuando se mueve)
			rotate_y(deg_to_rad(-event.relative.x * sens_horizontal))
			# Rotacion del eje Y de la "vista" con el mouse 
			visuals.rotate_y(deg_to_rad(event.relative.x * sens_horizontal))
			# Rotacion del eje X de la CAMARA usando el mouse
			camera_mount.rotate_x(deg_to_rad(-event.relative.y * sens_vertical))

func _physics_process(delta):
	# RECEPCION DE DATOS DEL LOCAL LOOP ###########################################################
	server.poll()
	if server.is_connection_available():
		var peer: PacketPeerUDP = server.take_connection()
		peers.append(peer)

	# Para cada cliente
	for i in range(0, peers.size()):
		if peers[i].get_available_packet_count() > 0:
			
			var packet = peers[i].get_packet()
			buffer.clear()
			buffer.data_array = packet
			
			Rx_pkts = Rx_pkts + 1
			pks_x_s = pks_x_s + 1
			
			for k in range(0, int(buffer.get_size() / 13)):
			# for k in range(0, int(buffer.get_size() / 12)):
			# for k in range(0, int(buffer.get_size() / 9)):
				s = buffer.get_u8()
				# No de paquete
				no_pkt = buffer.get_u32()
				
				# Quaternion w, x, y, z
				w = (buffer.get_16() / 16384.0) * q_mod[3]
				x = (buffer.get_16() / 16384.0) * q_mod[0]
				y = (buffer.get_16() / 16384.0) * q_mod[1]
				z = (buffer.get_16() / 16384.0) * q_mod[2]
				
				#w0 = (w0 / 16384.0) * q_mod[3]
				#x0 = (x0 / 16384.0) * q_mod[0]
				#y0 = (y0 / 16384.0) * q_mod[1]
				#z0 = (z0 / 16384.0) * q_mod[2]
				
				#w0 = buffer.get_16()
				#x0 = buffer.get_16()
				#y0 = buffer.get_16()
				#z0 = buffer.get_16()
				#w = (w0 / 16384.0) * q_mod[3]
				#x = (x0 / 16384.0) * q_mod[0]
				#y = (y0 / 16384.0) * q_mod[1]
				#z = (z0 / 16384.0) * q_mod[2]
				
				if x == 0.0 and y == 0.0 and z == 0.0 and w ==0.0:
					empy = true
					# print(w0, ", ", x0, ", ", y0, ", ", z0)
					# print(w, ", ", x, ", ", y, ", ", z)
				
				if not empy:
					empy = false
					hueso = id[s]
					rot_quat_0 = Quaternion(x, y, z, w).normalized()
					
					# DERECHA --------------------------------------------------
					# hombro
					if s == 0:
						rot_quat_2 = rot_quat_0 * QInv_0
						
					# codo
					if  s == 1:
						# Codo
						rot_quat_1 = skel.get_bone_pose_rotation(id[0])
						rot_quat_2 = rot_quat_1.inverse() * rot_quat_0 * QInv_1
					
					# muñeca
					if  s == 2:
						var rot_00 = skel.get_bone_pose_rotation(id[0]) 
						rot_quat_1 = skel.get_bone_pose_rotation(id[1])
						rot_quat_2 = rot_00.inverse() * rot_quat_1.inverse() * rot_quat_0 * QInv_2
					
					# IZQUIERDA ------------------------------------------------
					# hombro
					if s == 3:
						rot_quat_2 = rot_quat_0 * QInv_0
						
					# codo
					if  s == 4:
						# Codo
						rot_quat_1 = skel.get_bone_pose_rotation(id[3])
						rot_quat_2 = rot_quat_1.inverse() * rot_quat_0 * QInv_1
					
					# muñeca
					if  s == 5:
						var rot_00 = skel.get_bone_pose_rotation(id[3]) 
						rot_quat_1 = skel.get_bone_pose_rotation(id[4])
						rot_quat_2 = rot_00.inverse() * rot_quat_1.inverse() * rot_quat_0 * QInv_2
					
					# rot_quat_2 = rot_quat_0
					skel.set_bone_pose_rotation(hueso, rot_quat_2)
				
				# print(skel.get_bone_pose_rotation(id_0),skel.get_bone_pose_rotation(id_1), skel.get_bone_pose_rotation(id_2))


	count_frames = count_frames + 1
	if count_frames == Engine.physics_ticks_per_second:
		if pks_x_s > 0:
			print(Time.get_time_string_from_system(), "-", pks_x_s, " T=", Rx_pkts)
		count_frames = 0
		pks_x_s = 0

	if Input.is_action_pressed("run"):
		SPEED = walking_speed
		
	# Add the gravity.
	if not is_on_floor():
		velocity.y -= gravity * delta
	
	# Presionar "q" para sentar al personaje al no moverse
	if Input.is_action_just_pressed("sit"):
		pres_sit = !pres_sit
		print("Sit=", pres_sit)
	
	if Input.is_action_just_pressed("mouse"):
		if unlock_mouse:
			Input.mouse_mode = Input.MOUSE_MODE_CONFINED_HIDDEN
		else:
			Input.mouse_mode = Input.MOUSE_MODE_HIDDEN # El mouse puede salir de la ventana
		unlock_mouse = !unlock_mouse
		print("unlock_mouse:", unlock_mouse)
	
	if Input.is_action_just_pressed("fullscreen"):
		if DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
			DisplayServer.window_set_size(Vector2i(1280, 720))
		else:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
			
	# Click izquierdo para mover manualmente una parte con cuaterniones
	if Input.is_action_just_pressed("enter_quat"):
		"""
		# Obtener la rotacion actual del hueso
		var current_rotation = skel.get_bone_pose_rotation(id_0)
		
		# Formacion manual de cuaternion
		# var rotation_axis = Vector3(0, 1, 0)  # Eje de rotacion (En este caso Y)
		# var rotation_angle = deg_to_rad(45)  # Rotacion del eje
		# creacion del cuaternion (X, Y, Z, W) W=Angulo en radianes
		# var rotation_quat = Quaternion(rotation_axis, rotation_angle)
		
		# Cuaternion de Giro en eje Z del BNO
		var rotation_quat = Quaternion(0.2849 , 0.0111 , -0.0048 , 0.9584)
		
		# Nueva rotacion = Rotacion Pasada + Nueva (Se tienen que multiplicar)
		var new_rotation = current_rotation * rotation_quat
		
		# Aplicar la nueva rotación al hueso
		skel.set_bone_pose_rotation(id_0, new_rotation)
		"""
		reset_q = !reset_q
		print("Qinv=", reset_q)
		
		if reset_q:
			QInv_0 = skel.get_bone_pose_rotation(id[0])
			QInv_0 = QInv_0.inverse()
			
			QInv_1 = skel.get_bone_pose_rotation(id[1])
			QInv_1 = QInv_1.inverse()
			
			QInv_2 = skel.get_bone_pose_rotation(id[2])
			QInv_2 = QInv_2.inverse() # * Quaternion(0.70711, 0, 0, 0.70711)
		else:
			QInv_0 = identidad
			QInv_1 = identidad
			QInv_2 = identidad
									   # Quaternion(0, 0.70711, 0, 0.70711)
		inv_qua = rot_quat_0.inverse() * Quaternion(0.70711, 0, 0, 0.70711)

	# Al PRECIONAR TECLA DE ESPACIO
	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Get the input direction and handle the movement/deceleration.
	var input_dir = Input.get_vector("left", "right", "forward", "backward")
	var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	
	if direction:
		if animation_player.current_animation != "walking":
			animation_player.play("walking")

		# Para que el modelo mire en la direccion en la que se mueve
		visuals.look_at(position + direction)
		velocity.x = direction.x * SPEED
		velocity.z = direction.z * SPEED
	else:
		if pres_sit:
			if animation_player.current_animation != "sit":
				animation_player.play("sit")
		else:
			if animation_player.current_animation != "idle":
				animation_player.play("idle")
		velocity.x = move_toward(velocity.x, 0, SPEED)
		velocity.z = move_toward(velocity.z, 0, SPEED)

	move_and_slide()
