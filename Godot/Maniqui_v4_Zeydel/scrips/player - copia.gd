extends CharacterBody3D

# Importacion de la camara, esqueleto y animacion
@onready var camera_mount = $camera_mount
@onready var skel  = $visuals/mixamo_base/Armature/Skeleton3D
@onready var animation_player = $visuals/mixamo_base/AnimationPlayer
@onready var visuals = $visuals

# Exportacion de la sensibilidad horizontal y verticas (mov camara con mouse)
@export var sens_horizontal = 0.5
@export var sens_vertical = 0.5

# Crear un socket UDP
var server := UDPServer.new()
var puerto = 4000
var peers = [] #Lista de los nodos conectados
var buffer = StreamPeerBuffer.new()
var no_pkt = 0

var SPEED = 3.0
var running = false
var pres_sit = false
const JUMP_VELOCITY = 4.5
const walking_speed = 3.0
const running_speed = 5.0

# Ajuste de cuaternion del sensor para que coincidan los ejes
var NoSensores = 0
var q_mod = [1,-1,-1,1] # modificacion a cuaternion [x, y, z, w]
var rot_quat = Quaternion() # x, y, z, w
var w = 0.0
var x = 0.0
var y = 0.0
var z = 0.0

# Get the gravity from the project settings to be synced with RigidBody nodes.
var gravity = ProjectSettings.get_setting("physics/3d/default_gravity")
var id_0 = 0
var id_1 = 0
var hueso = 0

func _ready():
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	id_0 = skel.find_bone("mixamorig_RightArm")
	id_1 = skel.find_bone("mixamorig_RightForeArm")
	set_process(true)
	
	# Intentar conectar el socket al puerto en localhost
	var result = server.listen(puerto)
	if result != OK:
		print("Error al iniciar el servidor UDP: ", result)
	else:
		print("Servidor UDP iniciado en el puerto 5000, esperando datos...")
	
func _input(event):
	if event is InputEventMouseMotion:
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
			var packet = peers[i].get_packet()
			buffer.clear()
			buffer.data_array = packet
			
			for j in range(0, NoSensores):
				w = (buffer.get_16() / 10000.0) * q_mod[3]
				x = (buffer.get_16() / 10000.0) * q_mod[0]
				y = (buffer.get_16() / 10000.0) * q_mod[1]
				z = (buffer.get_16() / 10000.0) * q_mod[2]
			
				if j == 0:
					hueso = id_0
				if  j == 1:
					hueso = id_1
				
				skel.set_bone_pose_rotation(hueso, Quaternion(x, y, z, w))

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
		
	# Click izquierdo para mover manualmente una parte con cuaterniones
	if Input.is_action_just_pressed("enter_quat"):
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
