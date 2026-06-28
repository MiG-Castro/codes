extends CharacterBody3D

# Importacion de la camara, esqueleto y animacion
@onready var camera_mount = $camera_mount
@onready var skel  = $visuals/mixamo_base/Armature/Skeleton3D
@onready var animation_player = $visuals/mixamo_base/AnimationPlayer
@onready var visuals = $visuals

# Exportacion de la sensibilidad horizontal y verticas (mov camara con mouse)
@export var sens_horizontal = 0.5
@export var sens_vertical = 0.5

# Variables de movimiento
var gravity = ProjectSettings.get_setting("physics/3d/default_gravity")
var SPEED = 3.0
var running = false
const JUMP_VELOCITY = 4.5
const walking_speed = 3.0
const running_speed = 5.0
var target_position = Vector3(2.08,0,0) # Posicion para sentarse

# Variables banderas
var ResetPos = false	# AJUSTE A POSICION (VERTICAL) con "click izquierdo"
var sit = false			# Activacion con tecla "Q" -> Sienta el maniqui
var AutNoSamp = true	# Deteccion de numero de muestras por sensor automatico 

# Variables RECEPCION DE DATOS
var NoSensors = 3		# No. de sensores
var NoSamples = 6		# Muestras recibidas por sensor
var BytesxSample = 18	# Tamaño de paquete de cada muestra del sensor
var multiplo =  NoSamples * BytesxSample
var samp = 1
var num_pkt = 0;

# Almacenamiento de datos de los sensores
var SamplesS0 = []	# Hombro
var SamplesS1 = []	# Codo
var SamplesS2 = []	# muñeca
var SamplesS3 = []	# rodilla

# Crear un socket UDP
var server := UDPServer.new()
var puerto = 4000
var peers = [] #Lista de los nodos conectados
var buffer = StreamPeerBuffer.new()
var no_pkt = 0

# VARIABLES DE QUATERNIONES
var q_mod = [1,-1,-1,1]		# Ajuste a Q(XYZW) recibido 
var w = 0.0
var x = 0.0
var y = 0.0
var z = 0.0
var resta_Q = Quaternion()

# Referencia de posiciones
var identidad = Quaternion(0,0,0,1) # Equivalente a multiplicar por 1
var vertical_0 = Quaternion(0.70711, 0.00000, 0.00000, 0.70711) # Posicion vertical en brazo
var vertical_1 = Quaternion(-0.70711, 0.00000, 0.00000, 0.70711) # posicion vertical en rodilla


# Ultimo cuaternion recibido
var Qid_0 = Quaternion()
var Qid_1 = Quaternion()
var Qid_2 = Quaternion()
var Qid_3 = Quaternion()

# Quaterniones para ajustar a posicion especifica
var QInv_0 = Quaternion()
var QInv_1 = Quaternion()
var QInv_2 = Quaternion()
var QInv_3 = Quaternion()

# ID de HUESOS -> ARTICULACIONES
var id_0 = 0
var id_1 = 0
var id_2 = 0
var id_3 = 0

func _ready():
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	id_0 = skel.find_bone("mixamorig_RightArm")
	id_1 = skel.find_bone("mixamorig_RightForeArm")
	id_2 = skel.find_bone("mixamorig_RightHand")
	id_3 = skel.find_bone("mixamorig_RightLeg")
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
		if sit:
		# Rotacion del eje Y de la "vista" con el mouse 
			visuals.rotate_y(deg_to_rad(event.relative.x * sens_horizontal))
		# Rotacion del eje X de la CAMARA usando el mouse
		camera_mount.rotate_x(deg_to_rad(-event.relative.y * sens_vertical))

func _physics_process(delta):
	# Presionar "u" para sentar al personaje
	if Input.is_action_just_pressed("sit"):
		sit = !sit
		if sit:
			position = target_position
			rotation = Vector3(0, 0, 0)
		else:
			position = Vector3(0, 0, 0)
		
		# Limpiamos/reseteamos el registro
		SamplesS0.clear() # Hombro
		SamplesS1.clear() # Codo
		SamplesS2.clear() # muñeca
		SamplesS3.clear() # rodilla

	# RECEPCION DE DATOS DEL LOCAL LOOP ###########################################################
	server.poll() # Permite que se procesen nuevos paquetes
	if server.is_connection_available():
		var peer: PacketPeerUDP = server.take_connection() # peer es un objeto que representa la conexion del nodo
		peers.append(peer)  # revisar para borrar

	# Para cada cliente se obtienen los valores del paquete, se desglozan y froma el cueternion 
	for i in range(0, peers.size()):
		if peers[i].get_available_packet_count() > 0:
			var packet = peers[i].get_packet()
			
			# print(packet)
			# print("\n")
			
			buffer.clear()
			buffer.data_array = packet
			
			if AutNoSamp:
				NoSamples = packet.size() / (BytesxSample * NoSensors)
				multiplo =  NoSamples * BytesxSample
				# print(NoSamples)
			
			for j in range(NoSensors):
				for k in range(NoSamples):
					
					# Mueve el puntero del buffer al índice deseado
					buffer.seek(j * multiplo + k * BytesxSample)
					
					w = (buffer.get_16() / 10000.0) * q_mod[3]
					x = (buffer.get_16() / 10000.0) * q_mod[0]
					y = (buffer.get_16() / 10000.0) * q_mod[1]
					z = (buffer.get_16() / 10000.0) * q_mod[2]
					
					num_pkt = buffer.get_32() # primer set cuatro bytes basura
					num_pkt = buffer.get_32() # segundo set cuatro bytes No.Pkt
					print(num_pkt)
					
					
					if j == 0: # Hombro
						Qid_0 = Quaternion(x, y, z, w)
						SamplesS0.append(Qid_0)
					if j == 1: # Codo
						Qid_1 = Quaternion(x, y, z, w)
						SamplesS1.append(Qid_1)
						
					if j == 2: # Muñeca o rodilla
						if sit:
							# Quaternion para rodilla derecha
							Qid_3 = Quaternion(y, x, -1 * z, w)
							SamplesS3.append(Qid_3)
						else:
							Qid_2 = Quaternion(x, y, z, w)
							SamplesS2.append(Qid_2)
							
			# print(SamplesS0[0], SamplesS1[0])
	############################################################################
	# Despliegue de datos
	print(SamplesS0.size())
	# Articulacion primaria (HOMBRO)
	if SamplesS0.size() >= samp:
		if SamplesS0[0].length() > 0:
			skel.set_bone_pose_rotation(id_0, SamplesS0[0] * QInv_0)
		# Si ya se uso la muestra o es cero -> se elimina
		SamplesS0.remove_at(0)
		# SamplesS0.remove_at(1) 

	# Artuculacion secundaria (CODO)
	if SamplesS1.size() >= samp:
		if SamplesS1[0].length() > 0:
			# Obtenemos la rotacion de la articulacion primaria
			resta_Q = skel.get_bone_pose_rotation(id_0)
			# Restamos la rotacion a la obtenida por el sensor
			resta_Q = resta_Q.inverse() * SamplesS1[0]
			# Si esta activo, se hace el ajuste de rotacion (Qinv)
			skel.set_bone_pose_rotation(id_1, resta_Q * QInv_1)
		# Si ya se uso la muestra o es cero -> se elimina
		SamplesS1.remove_at(0)
		# SamplesS1.remove_at(1)

	# Articulacion terciaria (MUÑECA)
	if SamplesS2.size() >= samp and !sit:
		if  SamplesS2[0].length() > 0:
			# Obtenemos la rotacion de la articulacion primaria
			resta_Q = skel.get_bone_pose_rotation(id_0)
			# Restamos la rotacion a la obtenida por el sensor
			resta_Q = resta_Q.inverse() * SamplesS2[0]
			# Si esta activo, se hace el ajuste de rotacion (Qinv)
			skel.set_bone_pose_rotation(id_2, resta_Q * QInv_2)
		SamplesS2.remove_at(0) # Eliminamos la muestra
		#SamplesS2.remove_at(1) # Eliminamos la muestra

	# Articulacion inferior (RODILLA)
	if SamplesS3.size() >= samp and sit:
		if  SamplesS3[0].length() > 0:
			skel.set_bone_pose_rotation(id_3, SamplesS3[0] * QInv_3)
			skel.set_bone_pose_rotation(id_2, identidad)
		# Si ya se uso la muestra o es cero -> se elimina
		SamplesS3.remove_at(0)
		# SamplesS3.remove_at(1)

	if Input.is_action_pressed("run"):
		SPEED = running_speed
		running = true
	else:
		SPEED = walking_speed
		running = false
		
	# Add the gravity.
	if not is_on_floor():
		velocity.y -= gravity * delta

	if Input.is_action_just_pressed("AutNoSam"):
		AutNoSamp = !AutNoSamp

	# Click izquierdo para mover manualmente una parte con cuaterniones
	if Input.is_action_just_pressed("Reset_Pvertical"):
		ResetPos = !ResetPos
		# Si se activa el ajuste de posicion
		if ResetPos and SamplesS0.size() > 0:
			# Cambiamos el valor de QInv para iniciar en la posicion deseada
			QInv_0 = Qid_0.inverse() * vertical_0
			QInv_1 = Qid_1.inverse() * vertical_0
			QInv_2 = Qid_2.inverse() * vertical_0
			if sit:
				QInv_3 = Qid_3.inverse() * vertical_1
		else:
			# Cambiamos QInv=Qidentidad -> NO AFECTA
			QInv_0 = identidad
			QInv_1 = identidad
			QInv_2 = identidad
			QInv_3 = identidad
		
		print(ResetPos)
			
	# Al PRECIONAR TECLA DE ESPACIO
	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Get the input direction and handle the movement/deceleration.
	# As good practice, you should replace UI actions with custom gameplay actions.
	var input_dir = Input.get_vector("left", "right", "forward", "backward")
	var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	
	if direction and not sit:
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
		if sit:
			if animation_player.current_animation != "sit":
				animation_player.play("sit_2")
		else:
			if animation_player.current_animation != "idle":
				animation_player.play("idle")
		velocity.x = move_toward(velocity.x, 0, SPEED)
		velocity.z = move_toward(velocity.z, 0, SPEED)

	move_and_slide()
