extends CharacterBody3D

# Importacion de la camara, esqueleto y animacion
@onready var camera_mount = $camera_mount
@onready var skel  = $visuals/mixamo_base/Armature/Skeleton3D
@onready var animation_player = $visuals/mixamo_base/AnimationPlayer
@onready var visuals = $visuals

# Exportacion de la sensibilidad horizontal y verticas (mov camara con mouse)
@export var sens_horizontal = 0.5
@export var sens_vertical = 0.5

var mouse = false  # Bandera controlar limitaciones del mouse
 
# Crear un socket UDP
var server := UDPServer.new()
var puerto = 4000
var peers = [] #Lista de los nodos conectados
var buffer = StreamPeerBuffer.new()
var no_pkt = 0

var SPEED = 3.0
var running = false
var pres_sit = false
var inv_qua = Quaternion()
var reset_q = false
const JUMP_VELOCITY = 4.5
const walking_speed = 3.0
const running_speed = 5.0

# Ajuste de cuaternion del sensor para que coincidan los ejes
var vacio = false
var sensor_source = 0
var q_mod = [1,-1,-1,1] 
var rot_quat_0 = Quaternion() # x, y, z, w # Cuaternion Sensor
var rot_quat_1 = Quaternion() # x, y, z, w # Cuaternion articulacion anterior
var rot_quat_2 = Quaternion() # x, y, z, w # Cuaternion final (con resta)

# Referencia de posiciones
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
var id_0 = 0
var id_1 = 0
var id_2 = 0
var id_3 = 0

var Rx_pkts = 0
var count_frames = 0

func _ready():
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	id_0 = skel.find_bone("mixamorig_RightArm")
	id_1 = skel.find_bone("mixamorig_RightForeArm")
	#id_0 = skel.find_bone("mixamorig_LeftArm")
	#id_1 = skel.find_bone("mixamorig_LeftForeArm")
	
	id_2 = skel.find_bone("mixamorig_RightHand")
	id_3 = skel.find_bone("mixamorig_RightLeg")
	
	skel.set_bone_pose_rotation(id_0, Quaternion(0,0,0,1))
	skel.set_bone_pose_rotation(id_1, Quaternion(0,0,0,1))
	skel.set_bone_pose_rotation(id_2, Quaternion(0,0,0,1))
	
	set_process(true)
	
	# Intentar conectar el socket al puerto en localhost
	var result = server.listen(puerto)
	if result != OK:
		print("Error al iniciar el servidor UDP: ", result)
	else:
		print("Servidor UDP iniciado en el puerto 4000, esperando datos...")
	
func _input(event):
	if event is InputEventMouseMotion:
		if not mouse:
			# Rotacion del eje Y del MODELO con mouse (cuando se mueve)
			rotate_y(deg_to_rad(-event.relative.x * sens_horizontal))
			# Rotacion del eje Y de la "vista" con el mouse 
			visuals.rotate_y(deg_to_rad(event.relative.x * sens_horizontal))
			# Rotacion del eje X de la CAMARA usando el mouse
			camera_mount.rotate_x(deg_to_rad(-event.relative.y * sens_vertical))

func _physics_process(delta):	
	# RECEPCION DE DATOS DEL LOCAL LOOP ###########################################################
	server.poll() # Permite que se procesen nuevos paquetes
	if server.is_connection_available():
		var peer: PacketPeerUDP = server.take_connection() # peer es un objeto que representa la conexion del nodo
		peers.append(peer)  # revisar para borrar

	# Para cada cliente se obtienen los valores del paquete, se desglozan y froma el cueternion 
	for i in range(0, peers.size()):
		if peers[i].get_available_packet_count() > 0:
			# Aumento en el conteo de paquetes recibidos
			# Rx_pkts = Rx_pkts + 1
			
			var packet = peers[i].get_packet()
			buffer.clear()
			buffer.data_array = packet
			
			# for k in range(0, int(buffer.get_size() / 13)):
			for k in range(0, int(buffer.get_size() / 9)):
				sensor_source = buffer.get_u8()
				# No de paquete
				no_pkt = buffer.get_u32()
				
				# Quaternion w, x, y, z
				#w = (buffer.get_16() / 10000.0) * q_mod[3]
				#x = (buffer.get_16() / 10000.0) * q_mod[0]
				#y = (buffer.get_16() / 10000.0) * q_mod[1]
				#z = (buffer.get_16() / 10000.0) * q_mod[2]
				
				w = (buffer.get_16() / 16384.0) * q_mod[3]
				x = (buffer.get_16() / 16384.0) * q_mod[0]
				y = (buffer.get_16() / 16384.0) * q_mod[1]
				z = (buffer.get_16() / 16384.0) * q_mod[2]
				
				#w0 = buffer.get_16()
				#x0 = buffer.get_16()
				#y0 = buffer.get_16()
				#z0 = buffer.get_16()
				
				#w = (w0 / 16384.0) * q_mod[3]
				#x = (x0 / 16384.0) * q_mod[0]
				#y = (y0 / 16384.0) * q_mod[1]
				#z = (z0 / 16384.0) * q_mod[2]
				
				# print(w0, ", ", x0, ", ", y0, ", ", z0)
				
				if x == 0.0 and y == 0.0 and z == 0.0 and w ==0.0:
					vacio = true
				
				if not vacio:
					rot_quat_0 = Quaternion(x, y, z, w).normalized()
					
					if sensor_source == 0:
						# hombro
						hueso = id_0
						rot_quat_2 = rot_quat_0 * QInv_0
						# rot_quat_2 = Quaternion(-0.523056, 0.008728, 0.056517, 0.850378)
						# print(rot_quat_2, ", ", w0, ", ", x0, ", ", y0, ", ", z0)
						
					if  sensor_source == 1:
						# Codo
						hueso = id_1
						rot_quat_1 = skel.get_bone_pose_rotation(id_0)
						rot_quat_2 = rot_quat_1.inverse() * rot_quat_0 * QInv_1
						
					if  sensor_source == 2:
						# Muñeca
						hueso = id_2
						var rot_00 = skel.get_bone_pose_rotation(id_0) 
						rot_quat_1 = skel.get_bone_pose_rotation(id_1)
						rot_quat_2 = rot_00.inverse() * rot_quat_1.inverse() * rot_quat_0 * QInv_2
					
					# rot_quat_2 = rot_quat_0
					skel.set_bone_pose_rotation(hueso, rot_quat_2)
				
				vacio = false
				# print(skel.get_bone_pose_rotation(id_0),skel.get_bone_pose_rotation(id_1), skel.get_bone_pose_rotation(id_2))
	
	#count_frames = count_frames + 1
	#
	#if count_frames == 60:
		#var now = Time.get_datetime_dict_from_system()
		#var time_string = "%02d:%02d:%02d" % [now.hour, now.minute, now.second]
		#if Rx_pkts > 0:
			#print(time_string," - ", Rx_pkts)
		#count_frames = 0
		#Rx_pkts = 0

	if Input.is_action_pressed("run"):
		SPEED = running_speed
		running = true
	else:
		SPEED = walking_speed
		running = false
		
	# Add the gravity.
	if not is_on_floor():
		velocity.y -= gravity * delta
	
	# Presionar "q" para sentar al personaje al no moverse
	if Input.is_action_just_pressed("sit"):
		pres_sit = !pres_sit
		print(pres_sit)
	
	if Input.is_action_just_pressed("mouse"):
		if mouse:
			Input.mouse_mode = Input.MOUSE_MODE_CONFINED_HIDDEN
		else:
			Input.mouse_mode = Input.MOUSE_MODE_HIDDEN # El mouse puede salir de la ventana
		
		mouse = !mouse
		print(mouse)
	
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
		print(reset_q)
		
		if reset_q:
			QInv_0 = skel.get_bone_pose_rotation(id_0)
			QInv_0 = QInv_0.inverse()
			
			QInv_1 = skel.get_bone_pose_rotation(id_1)
			QInv_1 = QInv_1.inverse()
			
			QInv_2 = skel.get_bone_pose_rotation(id_2)
			QInv_2 = QInv_2.inverse() # * Quaternion(0.70711, 0, 0, 0.70711)
		else:
			QInv_0 = identidad
			QInv_1 = identidad
			QInv_2 = identidad
			
		inv_qua = rot_quat_0.inverse() * Quaternion(0.70711, 0, 0, 0.70711) #Quaternion(0, 0.70711, 0, 0.70711)
		

	# Al PRECIONAR TECLA DE ESPACIO
	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Get the input direction and handle the movement/deceleration.
	# As good practice, you should replace UI actions with custom gameplay actions.
	var input_dir = Input.get_vector("left", "right", "forward", "backward")
	var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	
	if direction:
		if running:
			if animation_player.current_animation != "running":
				animation_player.play("running")
		else:
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
