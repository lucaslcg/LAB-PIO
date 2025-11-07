import cv2
import numpy as np
import time
from multiprocessing import Pool
from picamera2 import Picamera2

# --- 1. CONFIGURAÇÕES PRINCIPAIS ---

# Dimensões da Captura
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Dimensões para Exibição (cada vídeo terá essa altura)
# A janela final terá (DISPLAY_WIDTH * 2, DISPLAY_HEIGHT)
DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 540

# Fonte para o texto no HUD
FONT = cv2.FONT_HERSHEY_SIMPLEX

# Limite mínimo de área do contorno para evitar ruído
MIN_AREA = 1000

# --- 2. CALIBRAÇÃO DE COR (VOCÊ PRECISA AJUSTAR ISSO!) ---

# Método 1: Faixas de Cor HSV (Mais Robusto)
# Formato: (H_min, S_min, V_min), (H_max, S_max, V_max)
HSV_RANGES = {
    'preto': ([0, 0, 0], [180, 255, 50]),
    'verde': ([35, 100, 100], [85, 255, 255]),
    # Vermelho passa pelo 0 do Hue, então precisamos de duas faixas
    'vermelho1': ([0, 100, 100], [10, 255, 255]),
    'vermelho2': ([170, 100, 100], [180, 255, 255])
}

# Método 2: Faixas de Cor BGR (Mais Rápido, Muito Frágil)
# Formato: (B_min, B_max), (G_min, G_max), (R_min, R_max)
BGR_RANGES = {
    'preto': ([0, 70], [0, 70], [0, 70]),
    'verde': ([0, 100], [120, 255], [0, 100]),
    'vermelho': ([0, 100], [0, 100], [120, 255])
}

# Cores para desenhar as "miras" (em BGR)
SIGHT_COLORS = {
    'preto': (100, 100, 100),
    'verde': (0, 255, 0),
    'vermelho': (0, 0, 255)
}

# --- 3. FUNÇÕES AUXILIARES ---

def find_and_draw_sights(frame, mask, name, color):
    """ Encontra o maior contorno na máscara e desenha a mira no frame """
    try:
        # Encontra contornos na máscara
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Encontra o MAIOR contorno baseado na área
            c = max(contours, key=cv2.contourArea)

            # Desenha apenas se for grande o suficiente para não ser ruído
            if cv2.contourArea(c) > MIN_AREA:
                (x, y, w, h) = cv2.boundingRect(c)
                # Desenha o retângulo (mira) e o rótulo da cor
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
                cv2.putText(frame, name, (x, y - 10), FONT, 0.8, color, 2)
    except:
        # Ignora erros que podem ocorrer se nenhum contorno for encontrado
        pass
    return frame

def draw_hud(frame, func_list, proc_time_ms):
    """ Desenha o HUD de performance (FPS, Custo, Funções) no frame """
    # Calcula o FPS Potencial (quantos frames por segundo este método rodaria sozinho)
    potential_fps = 1000.0 / proc_time_ms if proc_time_ms > 0 else float('inf')

    # Exibe FPS e Custo no canto superior direito
    cv2.putText(frame, f"FPS (Potencial): {potential_fps:.1f}", (FRAME_WIDTH - 350, 40), FONT, 0.9, (0, 255, 255), 2)
    cv2.putText(frame, f"Custo: {proc_time_ms:.2f} ms", (FRAME_WIDTH - 350, 80), FONT, 0.9, (0, 255, 255), 2)

    # Exibe a lista de funções usadas no canto inferior direito
    y_pos = FRAME_HEIGHT - 30
    for func_name in reversed(func_list):
        cv2.putText(frame, func_name, (FRAME_WIDTH - 450, y_pos), FONT, 0.7, (0, 255, 255), 2)
        y_pos -= 30
    return frame

# --- 4. FUNÇÕES DE PROCESSAMENTO (OS DOIS MÉTODOS) ---

def process_hsv(frame):
    """ Método 1: Tradicional com BGR2HSV """
    functions = ["cvtColor(BGR2HSV)", "inRange(x4)", "bitwise_or(x1)", "findContours(x3)"]
    t_start = cv2.getTickCount()

    # 1. Converter para HSV (melhor para detecção de cor)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 2. Criar máscaras para cada cor
    mask_preto = cv2.inRange(hsv, np.array(HSV_RANGES['preto'][0]), np.array(HSV_RANGES['preto'][1]))
    mask_verde = cv2.inRange(hsv, np.array(HSV_RANGES['verde'][0]), np.array(HSV_RANGES['verde'][1]))
    # Combina as duas faixas para a cor vermelha
    mask_vermelho = cv2.bitwise_or(cv2.inRange(hsv, np.array(HSV_RANGES['vermelho1'][0]), np.array(HSV_RANGES['vermelho1'][1])),
                                 cv2.inRange(hsv, np.array(HSV_RANGES['vermelho2'][0]), np.array(HSV_RANGES['vermelho2'][1])))

    # 3. Encontrar e desenhar as miras
    frame = find_and_draw_sights(frame, mask_preto, "PRETO", SIGHT_COLORS['preto'])
    frame = find_and_draw_sights(frame, mask_verde, "VERDE", SIGHT_COLORS['verde'])
    frame = find_and_draw_sights(frame, mask_vermelho, "VERMELHO", SIGHT_COLORS['vermelho'])

    # 4. Calcular tempo de processamento
    proc_time = ((cv2.getTickCount() - t_start) / cv2.getTickFrequency()) * 1000
    return frame, proc_time, functions

def process_bgr_split(frame):
    """ Método 2: Manipulação de canais BGR """
    functions = ["split(x1)", "inRange(x9)", "bitwise_and(x6)", "findContours(x3)"]
    t_start = cv2.getTickCount()

    # 1. Separar os canais B, G, R
    b, g, r = cv2.split(frame)

    # 2. Criar máscaras combinando os canais (frágil à iluminação)
    r_b, r_g, r_r = BGR_RANGES['preto']
    mask_preto = cv2.bitwise_and(cv2.inRange(b, r_b[0], r_b[1]), cv2.bitwise_and(cv2.inRange(g, r_g[0], r_g[1]), cv2.inRange(r, r_r[0], r_r[1])))

    r_b, r_g, r_r = BGR_RANGES['verde']
    mask_verde = cv2.bitwise_and(cv2.inRange(b, r_b[0], r_b[1]), cv2.bitwise_and(cv2.inRange(g, r_g[0], r_g[1]), cv2.inRange(r, r_r[0], r_r[1])))

    r_b, r_g, r_r = BGR_RANGES['vermelho']
    mask_vermelho = cv2.bitwise_and(cv2.inRange(b, r_b[0], r_b[1]), cv2.bitwise_and(cv2.inRange(g, r_g[0], r_g[1]), cv2.inRange(r, r_r[0], r_r[1])))

    # 3. Encontrar e desenhar as miras
    frame = find_and_draw_sights(frame, mask_preto, "PRETO", SIGHT_COLORS['preto'])
    frame = find_and_draw_sights(frame, mask_verde, "VERDE", SIGHT_COLORS['verde'])
    frame = find_and_draw_sights(frame, mask_vermelho, "VERMELHO", SIGHT_COLORS['vermelho'])

    # 4. Calcular tempo de processamento
    proc_time = ((cv2.getTickCount() - t_start) / cv2.getTickFrequency()) * 1000
    return frame, proc_time, functions

# --- 5. LOOP PRINCIPAL DE COMPARAÇÃO ---
def run_comparison():
    print("Iniciando a câmera com Picamera2...")
    picam2 = Picamera2()
    # Configura a câmera para um modo compatível com o OpenCV (BGR888) e com a resolução desejada
    config = picam2.create_preview_configuration(main={"format": "BGR888", "size": (FRAME_WIDTH, FRAME_HEIGHT)})
    picam2.configure(config)
    picam2.start()

    print(f"Câmera aberta. Resolução: {FRAME_WIDTH}x{FRAME_HEIGHT}")
    print("Pressione 'q' para sair.")
    time.sleep(1.0) # Aguarda a câmera estabilizar

    # Cria um pool de processos para executar os métodos de visão em paralelo
    with Pool(processes=2) as pool:
        while True:
            # 1. Captura o frame como um array NumPy, pronto para o OpenCV
            frame = picam2.capture_array()

            if frame is None:
                print("Erro ao capturar o frame com Picamera2.")
                continue

            # 2. Envia uma cópia do frame para cada processo do pool
            async_hsv = pool.apply_async(process_hsv, (frame.copy(),))
            async_bgr = pool.apply_async(process_bgr_split, (frame.copy(),))

            # 3. Aguarda os resultados dos dois processos
            frame_hsv, time_hsv, funcs_hsv = async_hsv.get()
            frame_bgr, time_bgr, funcs_bgr = async_bgr.get()

            # 4. Desenha os HUDs de performance em cada frame processado
            frame_hsv = draw_hud(frame_hsv, funcs_hsv, time_hsv)
            frame_bgr = draw_hud(frame_bgr, funcs_bgr, time_bgr)

            # 5. Redimensiona os frames para exibição
            display_hsv = cv2.resize(frame_hsv, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
            display_bgr = cv2.resize(frame_bgr, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

            # Adiciona rótulos aos vídeos
            cv2.putText(display_hsv, "METODO 1: BGR2HSV (Paralelo)", (20, 40), FONT, 1.2, (255, 255, 0), 3)
            cv2.putText(display_bgr, "METODO 2: BGR-SPLIT (Paralelo)", (20, 40), FONT, 1.2, (255, 255, 0), 3)

            # 6. Combina os dois vídeos lado a lado e exibe
            combined_output = np.hstack((display_hsv, display_bgr))
            cv2.imshow("Comparacao de Metodos (Picamera2) - Pressione 'q' para sair", combined_output)

            # 7. Verifica se o usuário quer sair
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # --- Limpeza ---
    print("Encerrando...")
    picam2.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_comparison()
