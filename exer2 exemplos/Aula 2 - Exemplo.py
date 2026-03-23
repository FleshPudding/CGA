# Câmera e exemplo base para a disciplina de Computação Gráfica em Tempo Real e Computação Gráfica Avançada
#
# Este código serve como base para toda a disciplina.
# Ele implementa:
# - OpenGL moderno (pipeline programável)
# - Um modelo geométrico simples (cubo)
# - Transformações de modelo, visualização (câmera) e projeção
# - Uma câmera no estilo FPS (yaw + pitch)
#
# A partir deste exemplo, novos conceitos serão adicionados gradualmente
# (iluminação, materiais, texturas, visibilidade, sombras, etc.)

import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np

Window = None
Shader_programm = None
Vao_cubo = None

WIDTH = 800
HEIGHT = 600

Tempo_entre_frames = 0.0

# -----------------------------
# Parâmetros da câmera virtual
# -----------------------------

Cam_speed = 10.0          # velocidade de deslocamento da câmera
Cam_yaw_speed = 30.0      # velocidade de rotação horizontal
Cam_pos = np.array([0.0, 0.0, 2.0])  # posição inicial da câmera
Cam_yaw = 0.0             # rotação horizontal
Cam_pitch = 0.0           # rotação vertical

lastX, lastY = WIDTH / 2, HEIGHT / 2
primeiro_mouse = True

# -----------------------------
# Callbacks de janela e entrada
# -----------------------------

def redimensionaCallback(window, w, h):
    global WIDTH, HEIGHT
    WIDTH = w
    HEIGHT = h

def mouse_callback(window, xpos, ypos):
    global lastX, lastY, primeiro_mouse, Cam_yaw, Cam_pitch

    if primeiro_mouse:
        lastX, lastY = xpos, ypos
        primeiro_mouse = False

    xoffset = xpos - lastX
    yoffset = lastY - ypos
    lastX, lastY = xpos, ypos

    sensibilidade = 0.1
    xoffset *= sensibilidade
    yoffset *= sensibilidade

    Cam_yaw += xoffset
    Cam_pitch += yoffset

    Cam_pitch = max(-89.0, min(89.0, Cam_pitch))

def key_callback(window, key, scancode, action, mode):
    return

# -----------------------------
# Inicialização do OpenGL
# -----------------------------

def inicializaOpenGL():
    global Window

    #inicializa a GLFW
    glfw.init()

    #Cria uma janela
    Window = glfw.create_window(WIDTH, HEIGHT, "Exemplo Base - CG em Tempo Real", None, None)
    if not Window:
        glfw.terminate()
        exit()

    glfw.set_window_size_callback(Window, redimensionaCallback)
    glfw.set_cursor_pos_callback(Window, mouse_callback)
    glfw.set_key_callback(Window, key_callback)
    
    glfw.make_context_current(Window)
    glfw.set_input_mode(Window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    

    print("Placa de vídeo:", glGetString(GL_RENDERER))
    print("Versão do OpenGL:", glGetString(GL_VERSION))

# -----------------------------
# Inicialização da geometria
# -----------------------------
# Aqui criamos o MODELO geométrico.
# O cubo é definido uma única vez e pode ser instanciado várias vezes na cena.

def inicializaCubo():
    global Vao_cubo

    # 36 vértices (6 faces, 2 triângulos por face)
    points = [
        #x     y    z       x   y       z      x    y      z
        # face frontal
        0.5,  0.5,  0.5,   0.5, -0.5,  0.5,  -0.5, -0.5,  0.5,
        0.5,  0.5,  0.5,  -0.5, -0.5,  0.5,  -0.5,  0.5,  0.5,
        # face traseira
        0.5,  0.5, -0.5,   0.5, -0.5, -0.5,  -0.5, -0.5, -0.5,
        0.5,  0.5, -0.5,  -0.5, -0.5, -0.5,  -0.5,  0.5, -0.5,
        # face esquerda
       -0.5, -0.5,  0.5,  -0.5,  0.5,  0.5,  -0.5, -0.5, -0.5,
       -0.5, -0.5, -0.5,  -0.5,  0.5, -0.5,  -0.5,  0.5,  0.5,
        # face direita
        0.5, -0.5,  0.5,   0.5,  0.5,  0.5,   0.5, -0.5, -0.5,
        0.5, -0.5, -0.5,   0.5,  0.5, -0.5,   0.5,  0.5,  0.5,
        # face inferior
       -0.5, -0.5,  0.5,   0.5, -0.5,  0.5,   0.5, -0.5, -0.5,
        0.5, -0.5, -0.5,  -0.5, -0.5, -0.5,  -0.5, -0.5,  0.5,
        # face superior
       -0.5,  0.5,  0.5,   0.5,  0.5,  0.5,   0.5,  0.5, -0.5,
        0.5,  0.5, -0.5,  -0.5,  0.5, -0.5,  -0.5,  0.5,  0.5,
    ]

    points = np.array(points, dtype=np.float32)
    
    #Gera o VAO do cubo
    Vao_cubo = glGenVertexArrays(1)
    glBindVertexArray(Vao_cubo)
    
    #Gera o VBO e transfere os vértices para ele
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, points, GL_STATIC_DRAW)

    #Ativa o VBO de índice 0, pois é o único do cubo
    glEnableVertexAttribArray(0)
    #Configura o VBO a partir da posição 0 da lista de vértices, 3 a 3 (pois é x, y e z)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

# -----------------------------
# Shaders
# -----------------------------
# O shader está preparado semanticamente para crescer.
# No momento, não há iluminação nem textura.

def inicializaShaders():
    global Shader_programm
    #Vertex Shader calcula a posição final de cada vértice com base:
    # 1--> nos vértices do modelo
    # 2--> transformações geométricas aplicadas ao modelo
    # 3--> posição da câmera
    # 4--> tipo de projeção
    vertex_shader = """
        #version 400
        layout(location = 0) in vec3 vertex_posicao;

        // transform -> matriz de modelo (objeto -> mundo)
        // view      -> matriz da câmera (mundo -> câmera)
        // proj      -> matriz de projeção (câmera -> recorte)
        uniform mat4 transform;
        uniform mat4 view;
        uniform mat4 proj;

        void main() {
            gl_Position = proj * view * transform * vec4(vertex_posicao, 1.0);
        }
    """
    #Fragment Shader
    fragment_shader = """
        #version 400
        out vec4 frag_colour;
        uniform vec4 corobjeto;

        void main() {
            frag_colour = corobjeto;
        }
    """

    #Compila o vertex e fragment shader, e depois linka eles em um shader program
    vs = OpenGL.GL.shaders.compileShader(vertex_shader, GL_VERTEX_SHADER)
    fs = OpenGL.GL.shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER)
    Shader_programm = OpenGL.GL.shaders.compileProgram(vs, fs)

    glDeleteShader(vs)
    glDeleteShader(fs)

# -----------------------------
# Transformação de modelo
# -----------------------------
# Define a INSTÂNCIA do modelo no mundo.

def transformacaoGenerica(Tx, Ty, Tz, Sx, Sy, Sz, Rx, Ry, Rz):
    translacao = np.array([
        [1, 0, 0, Tx],
        [0, 1, 0, Ty],
        [0, 0, 1, Tz],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    rx, ry, rz = np.radians([Rx, Ry, Rz])

    #pitch
    rotX = np.array([
        [1, 0, 0, 0],
        [0, np.cos(rx), -np.sin(rx), 0],
        [0, np.sin(rx),  np.cos(rx), 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    #yaw
    rotY = np.array([
        [ np.cos(ry), 0, np.sin(ry), 0],
        [0, 1, 0, 0],
        [-np.sin(ry), 0, np.cos(ry), 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    #roll
    rotZ = np.array([
        [np.cos(rz), -np.sin(rz), 0, 0],
        [np.sin(rz),  np.cos(rz), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    escala = np.array([
        [Sx, 0, 0, 0],
        [0, Sy, 0, 0],
        [0, 0, Sz, 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    transform = translacao @ rotZ @ rotY @ rotX @ escala

    loc = glGetUniformLocation(Shader_programm, "transform")
    glUniformMatrix4fv(loc, 1, GL_TRUE, transform)

# -----------------------------
# Câmera (matriz de visualização)
# -----------------------------

def especificaMatrizVisualizacao():
    global Cam_pos, Cam_yaw, Cam_pitch

    front = np.array([
        np.cos(np.radians(Cam_yaw)) * np.cos(np.radians(Cam_pitch)),
        np.sin(np.radians(Cam_pitch)),
        np.sin(np.radians(Cam_yaw)) * np.cos(np.radians(Cam_pitch))
    ])
    front /= np.linalg.norm(front)

    up = np.array([0.0, 1.0, 0.0])
    s = np.cross(front, up)
    s /= np.linalg.norm(s)
    u = np.cross(s, front)

    view = np.identity(4, dtype=np.float32)
    view[0, :3] = s
    view[1, :3] = u
    view[2, :3] = -front
    view[0, 3] = -np.dot(s, Cam_pos)
    view[1, 3] = -np.dot(u, Cam_pos)
    view[2, 3] =  np.dot(front, Cam_pos)

    loc = glGetUniformLocation(Shader_programm, "view")
    glUniformMatrix4fv(loc, 1, GL_TRUE, view)

# -----------------------------
# Projeção
# -----------------------------

def especificaMatrizProjecao():
    znear, zfar = 0.1, 100.0
    fov = np.radians(67.0)
    aspecto = WIDTH / HEIGHT

    a = 1 / (np.tan(fov / 2) * aspecto)
    b = 1 / np.tan(fov / 2)
    c = (zfar + znear) / (znear - zfar)
    d = (2 * znear * zfar) / (znear - zfar)

    proj = np.array([
        [a, 0, 0, 0],
        [0, b, 0, 0],
        [0, 0, c, d],
        [0, 0, -1, 1]
    ], dtype=np.float32)

    loc = glGetUniformLocation(Shader_programm, "proj")
    glUniformMatrix4fv(loc, 1, GL_TRUE, proj)

def inicializaCamera():
    especificaMatrizVisualizacao()
    especificaMatrizProjecao()

# -----------------------------
# Entrada de teclado
# -----------------------------

def trataTeclado():
    global Cam_pos, Tempo_entre_frames

    velocidade = Cam_speed * Tempo_entre_frames

    frente = np.array([
        np.cos(np.radians(Cam_yaw)) * np.cos(np.radians(Cam_pitch)),
        np.sin(np.radians(Cam_pitch)),
        np.sin(np.radians(Cam_yaw)) * np.cos(np.radians(Cam_pitch))
    ])
    frente /= np.linalg.norm(frente)

    direita = np.cross(frente, np.array([0.0, 1.0, 0.0]))
    direita /= np.linalg.norm(direita)

    if glfw.get_key(Window, glfw.KEY_W) == glfw.PRESS:
        Cam_pos += frente * velocidade
    if glfw.get_key(Window, glfw.KEY_S) == glfw.PRESS:
        Cam_pos -= frente * velocidade
    if glfw.get_key(Window, glfw.KEY_A) == glfw.PRESS:
        Cam_pos -= direita * velocidade
    if glfw.get_key(Window, glfw.KEY_D) == glfw.PRESS:
        Cam_pos += direita * velocidade
    if glfw.get_key(Window, glfw.KEY_ESCAPE) == glfw.PRESS:
        glfw.set_window_should_close(Window, True)

# -----------------------------
# Renderização
# -----------------------------

def inicializaRenderizacao():
    global Tempo_entre_frames

    tempo_anterior = glfw.get_time()

    glEnable(GL_DEPTH_TEST)

    while not glfw.window_should_close(Window):
        tempo_atual = glfw.get_time()
        Tempo_entre_frames = tempo_atual - tempo_anterior
        tempo_anterior = tempo_atual

        #Limpa a tela e os buffers
        glClearColor(0.2, 0.3, 0.3, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glViewport(0, 0, WIDTH, HEIGHT)

        #Ativa o shader
        glUseProgram(Shader_programm)
        
        #Configura a câmera
        inicializaCamera()

        #Coloca o VAO do Cubo no topo da máquina de estados do OpenGL
        glBindVertexArray(Vao_cubo)


        defineCor(1.0, 0.6, 0.2, 1.0)
        transformacaoGenerica(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0, 0, 0)
        glDrawArrays(GL_TRIANGLES, 0, 36)

        glfw.swap_buffers(Window)
        glfw.poll_events()
        trataTeclado()

    glfw.terminate()

def defineCor(r, g, b, a):
    cor = np.array([r, g, b, a], dtype=np.float32)
    loc = glGetUniformLocation(Shader_programm, "corobjeto")
    glUniform4fv(loc, 1, cor)

# -----------------------------
# Função principal
# -----------------------------

def main():
    inicializaOpenGL()
    inicializaCubo()
    inicializaShaders()
    inicializaRenderizacao()

if __name__ == "__main__":
    main()