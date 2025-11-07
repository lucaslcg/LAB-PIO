import cv2
import numpy as np
import time
from multiprocessing import Pool

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
HSV_RANGES = {
    'preto': ([0, 0, 0], [180, 255, 50]),
    'verde': ([35, 100, 100], [85, 255, 255]),
    'vermelho1': ([0, 100, 100], [10, 255, 255]),
    'vermelho2': ([170, 100, 100], [180, 255, 255])
}

# Método 2: Faixas de Cor BGR (Mais Rápido, Muito Frágil)
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
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            if area > MIN_AREA:
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
                cv2.putText(frame, name, (x, y - 10), FONT, 0.8, color, 2)
    except:
        pass
    return frame

def draw_hud(frame, func_list, proc_time_ms):
    """ Desenha o HUD de performance (FPS, Custo, Funções) no frame """
    if proc_time_ms > 0:
        potential_fps = 1000.0 / proc_time_ms
    else:
        potential_fps = float('inf')
        
    text_fps = f"FPS (Potencial): {potential_fps:.1f}"
    text_cost = f"Custo: {proc_time_ms:.2f} ms"
    
    cv2.putText(frame, text_fps, (FRAME_WIDTH - 350, 40), FONT, 0.9, (0, 255, 255), 2)
    cv2.putText(frame, text_cost, (FRAME_WIDTH - 350, 80), FONT, 0.9, (0, 255, 255), 2)
    
    y_pos = FRAME_HEIGHT - 30
    for func_name in reversed(func_list):
        cv2.putText(frame, func_name, (FRAME_WIDTH - 450, y_pos), FONT, 0.7, (0, 255, 255), 2)
        y_pos -= 30
    return frame

# --- 4. FUNÇÕES DE PROCESSAMENTO (OS DOIS MÉTODOS) ---

def process_hsv(frame):
    """ Método 1: Tradicional com BGR2HSV """
    functions_used = [
        "cvtColor(BGR2HSV)", "inRange (x4)", "bitwise_or (x1)",
        "findContours (x3)", "contourArea (x3)", "boundingRect (x3)"
    ]
    t_start = cv2.getTickCount()
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask_preto = cv2.inRange(hsv, np.array(HSV_RANGES['preto'][0]), np.array(HSV_RANGES['preto'][1]))
    mask_verde = cv2.inRange(hsv, np.array(HSV_RANGES['verde'][0]), np.array(HSV_RANGES['verde'][1]))
    mask_vermelho1 = cv2.inRange(hsv, np.array(HSV_RANGES['vermelho1'][0]), np.array(HSV_RANGES['vermelho1'][1]))
    mask_vermelho2 = cv2.inRange(hsv, np.array(HSV_RANGES['vermelho2'][0]), np.array(HSV_RANGES['vermelho2'][1]))
    mask_vermelho = cv2.bitwise_or(mask_vermelho1, mask_vermelho2)
    
    frame = find_and_draw_sights(frame, mask_preto, "PRETO", SIGHT_COLORS['preto'])
    frame = find_and_draw_sights(frame, mask_verde, "VERDE", SIGHT_COLORS['verde'])
    frame = find_and_draw_sights(frame, mask_vermelho, "VERMELHO", SIGHT_COLORS['vermelho'])

    proc_time_ms = ((cv2.getTickCount() - t_start) / cv2.getTickFrequency()) * 1000
    return frame, proc_time_ms, functions_used

def process_bgr_split(frame):
    """ Método 2: Manipulação de canais BGR """
    functions_used = [
        "split (x1)", "inRange (x9)", "bitwise_and (x6)",
        "findContours (x3)", "contourArea (x3)", "boundingRect (x3)"
    ]
    t_start = cv2.getTickCount()
    
    b_channel, g_channel, r_channel = cv2.split(frame)
    
    r_b, r_g, r_r = BGR_RANGES['preto']
    b_mask = cv2.inRange(b_channel, r_b[0], r_b[1])
    g_mask = cv2.inRange(g_channel, r_g[0], r_g[1])
    r_mask = cv2.inRange(r_channel, r_r[0], r_r[1])
    mask_preto = cv2.bitwise_and(b_mask, cv2.bitwise_and(g_mask, r_mask))
    
    r_b, r_g, r_r = BGR_RANGES['verde']
    b_mask = cv2.inRange(b_channel, r_b[0], r_b[1])
    g_mask = cv2.inRange(g_channel, r_g[0], r_g[1])
    r_mask = cv2.inRange(r_channel, r_r[0], r_r[1])
    mask_verde = cv2.bitwise_and(b_mask, cv2.bitwise_and(g_mask, r_mask))

    r_b, r_g, r_r = BGR_RANGES['vermelho']
    b_mask = cv2.inRange(b_channel, r_b[0], r_b[1])
    g_mask = cv2.inRange(g_channel, r_g[0], r_g[1])
    r_mask = cv2.inRange(r_channel, r_r[0], r_r[1])
    mask_vermelho = cv2.bitwise_and(b_mask, cv2.bitwise_and(g_mask, r_mask))
    
    frame = find_and_draw_sights(frame, mask_preto, "PRETO", SIGHT_COLORS['preto'])
    frame = find_and_draw_sights(frame, mask_verde, "VERDE", SIGHT_COLORS['verde'])
    frame = find_and_draw_sights(frame, mask_vermelho, "VERMELHO", SIGHT_COLORS['vermelho'])

    proc_time_ms = ((cv2.getTickCount() - t_start) / cv2.getTickFrequency()) * 1000
    return frame, proc_time_ms, functions_used

# --- 5. LOOP PRINCIPAL DE COMPARAÇÃO ---

def run_comparison():
    print("Iniciando a captura da câmera...")
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print("Erro: Não foi possível abrir a câmera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    print("Aguardando a câmera estabilizar...")
    time.sleep(1.0)

    print(f"Câmera aberta. Resolução: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
    print("Pressione 'q' para sair.")

    # Cria um pool com 2 processos para executar os métodos em paralelo
    with Pool(processes=2) as pool:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Erro ao ler o frame.")
                break

            # Inicia os dois métodos em processos separados
            async_hsv = pool.apply_async(process_hsv, (frame.copy(),))
            async_bgr = pool.apply_async(process_bgr_split, (frame.copy(),))

            # Aguarda e obtém os resultados
            frame_hsv, time_hsv, funcs_hsv = async_hsv.get()
            frame_bgr, time_bgr, funcs_bgr = async_bgr.get()

            # Desenha os HUDs de performance nos frames processados
            frame_hsv = draw_hud(frame_hsv, funcs_hsv, time_hsv)
            frame_bgr = draw_hud(frame_bgr, funcs_bgr, time_bgr)

            # Redimensiona para exibição
            display_hsv = cv2.resize(frame_hsv, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
            display_bgr = cv2.resize(frame_bgr, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

            cv2.putText(display_hsv, "METODO 1: BGR2HSV (Paralelo)", (20, 40), FONT, 1.2, (255, 255, 0), 3)
            cv2.putText(display_bgr, "METODO 2: BGR-SPLIT (Paralelo)", (20, 40), FONT, 1.2, (255, 255, 0), 3)

            combined_output = np.hstack((display_hsv, display_bgr))

            cv2.imshow("Comparacao de Metodos (Paralelo) - Pressione 'q' para sair", combined_output)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    print("Encerrando...")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_comparison()
