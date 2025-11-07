import cv2
import numpy as np

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
        # Encontra contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 0:
            # Encontra o MAIOR contorno
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            
            # Desenha apenas se for grande o suficiente
            if area > MIN_AREA:
                # Pega o retângulo que envolve o contorno
                (x, y, w, h) = cv2.boundingRect(c)
                
                # Desenha a "mira" (retângulo)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
                # Desenha o rótulo
                cv2.putText(frame, name, (x, y - 10), FONT, 0.8, color, 2)
    except:
        pass # Ignora erros de contorno

def draw_hud(frame, func_list, proc_time_ms):
    """ Desenha o HUD de performance (FPS, Custo, Funções) no frame """
    
    # --- Canto Superior Direito: FPS e Custo ---
    
    # Calcula o FPS Potencial (quantos frames por segundo este método rodaria)
    if proc_time_ms > 0:
        potential_fps = 1000.0 / proc_time_ms
    else:
        potential_fps = float('inf')
        
    text_fps = f"FPS (Potencial): {potential_fps:.1f}"
    text_cost = f"Custo: {proc_time_ms:.2f} ms"
    
    cv2.putText(frame, text_fps, (FRAME_WIDTH - 350, 40), FONT, 0.9, (0, 255, 255), 2)
    cv2.putText(frame, text_cost, (FRAME_WIDTH - 350, 80), FONT, 0.9, (0, 255, 255), 2)
    
    # --- Canto Inferior Direito: Lista de Funções ---
    
    # Define a posição inicial Y (de baixo para cima)
    y_pos = FRAME_HEIGHT - 30
    
    for func_name in reversed(func_list):
        cv2.putText(frame, func_name, (FRAME_WIDTH - 450, y_pos), FONT, 0.7, (0, 255, 255), 2)
        y_pos -= 30 # Sobe para a próxima linha

# --- 4. FUNÇÕES DE PROCESSAMENTO (OS DOIS MÉTODOS) ---

def process_hsv(frame):
    """ Método 1: Tradicional com BGR2HSV """
    
    # Lista de funções para o HUD
    functions_used = [
        "cvtColor(BGR2HSV)",
        "inRange (x4)",
        "bitwise_or (x1)",
        "findContours (x3)",
        "contourArea (x3)",
        "boundingRect (x3)"
    ]
    
    # Inicia a contagem de tempo
    t_start = cv2.getTickCount()
    
    # 1. Converter para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 2. Criar máscaras
    mask_preto = cv2.inRange(hsv, np.array(HSV_RANGES['preto'][0]), np.array(HSV_RANGES['preto'][1]))
    mask_verde = cv2.inRange(hsv, np.array(HSV_RANGES['verde'][0]), np.array(HSV_RANGES['verde'][1]))
    
    # 3. Máscara de vermelho (duas faixas)
    mask_vermelho1 = cv2.inRange(hsv, np.array(HSV_RANGES['vermelho1'][0]), np.array(HSV_RANGES['vermelho1'][1]))
    mask_vermelho2 = cv2.inRange(hsv, np.array(HSV_RANGES['vermelho2'][0]), np.array(HSV_RANGES['vermelho2'][1]))
    mask_vermelho = cv2.bitwise_or(mask_vermelho1, mask_vermelho2)
    
    # 4. Encontrar e desenhar miras
    find_and_draw_sights(frame, mask_preto, "PRETO", SIGHT_COLORS['preto'])
    find_and_draw_sights(frame, mask_verde, "VERDE", SIGHT_COLORS['verde'])
    find_and_draw_sights(frame, mask_vermelho, "VERMELHO", SIGHT_COLORS['vermelho'])

    # 5. Finalizar contagem de tempo
    t_end = cv2.getTickCount()
    proc_time_ms = ((t_end - t_start) / cv2.getTickFrequency()) * 1000
    
    return frame, proc_time_ms, functions_used

def process_bgr_split(frame):
    """ Método 2: Manipulação de canais BGR """
    
    # Lista de funções para o HUD
    functions_used = [
        "split (x1)",
        "inRange (x9)",
        "bitwise_and (x6)",
        "findContours (x3)",
        "contourArea (x3)",
        "boundingRect (x3)"
    ]

    # Inicia a contagem de tempo
    t_start = cv2.getTickCount()
    
    # 1. Separar canais
    b_channel, g_channel, r_channel = cv2.split(frame)
    
    # 2. Criar máscara para PRETO
    r_b, r_g, r_r = BGR_RANGES['preto']
    b_mask = cv2.inRange(b_channel, r_b[0], r_b[1])
    g_mask = cv2.inRange(g_channel, r_g[0], r_g[1])
    r_mask = cv2.inRange(r_channel, r_r[0], r_r[1])
    mask_preto = cv2.bitwise_and(b_mask, cv2.bitwise_and(g_mask, r_mask))
    
    # 3. Criar máscara para VERDE
    r_b, r_g, r_r = BGR_RANGES['verde']
    b_mask = cv2.inRange(b_channel, r_b[0], r_b[1])
    g_mask = cv2.inRange(g_channel, r_g[0], r_g[1])
    r_mask = cv2.inRange(r_channel, r_r[0], r_r[1])
    mask_verde = cv2.bitwise_and(b_mask, cv2.bitwise_and(g_mask, r_mask))

    # 4. Criar máscara para VERMELHO
    r_b, r_g, r_r = BGR_RANGES['vermelho']
    b_mask = cv2.inRange(b_channel, r_b[0], r_b[1])
    g_mask = cv2.inRange(g_channel, r_g[0], r_g[1])
    r_mask = cv2.inRange(r_channel, r_r[0], r_r[1])
    mask_vermelho = cv2.bitwise_and(b_mask, cv2.bitwise_and(g_mask, r_mask))
    
    # 5. Encontrar e desenhar miras
    find_and_draw_sights(frame, mask_preto, "PRETO", SIGHT_COLORS['preto'])
    find_and_draw_sights(frame, mask_verde, "VERDE", SIGHT_COLORS['verde'])
    find_and_draw_sights(frame, mask_vermelho, "VERMELHO", SIGHT_COLORS['vermelho'])

    # 6. Finalizar contagem de tempo
    t_end = cv2.getTickCount()
    proc_time_ms = ((t_end - t_start) / cv2.getTickFrequency()) * 1000
    
    return frame, proc_time_ms, functions_used

# --- 5. LOOP PRINCIPAL DE COMPARAÇÃO ---

def run_comparison():
    print("Iniciando a captura da câmera...")
    # Tenta usar GStreamer para melhor performance no RPi, se falhar, usa o 0
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Erro: Não foi possível abrir a câmera.")
        return

    # Define a resolução da CÂMERA
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    print(f"Câmera aberta. Resolução: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
    print("Pressione 'q' para sair.")

    while True:
        # 1. Captura o frame
        ret, frame = cap.read()
        if not ret:
            print("Erro ao ler o frame.")
            break
            
        # 2. Cria cópias para cada método
        frame_hsv = frame.copy()
        frame_bgr = frame.copy()

        # 3. Processa pelos dois métodos e mede o tempo
        frame_hsv, time_hsv, funcs_hsv = process_hsv(frame_hsv)
        frame_bgr, time_bgr, funcs_bgr = process_bgr_split(frame_bgr)
        
        # 4. Desenha os HUDs de performance
        draw_hud(frame_hsv, funcs_hsv, time_hsv)
        draw_hud(frame_bgr, funcs_bgr, time_bgr)
        
        # 5. Redimensiona os frames para exibição
        display_hsv = cv2.resize(frame_hsv, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        display_bgr = cv2.resize(frame_bgr, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

        # Adiciona rótulos aos vídeos
        cv2.putText(display_hsv, "METODO 1: BGR2HSV (Robusto)", (20, 40), FONT, 1.2, (255, 255, 0), 3)
        cv2.putText(display_bgr, "METODO 2: BGR-SPLIT (Fragil)", (20, 40), FONT, 1.2, (255, 255, 0), 3)
        
        # 6. Combina os dois vídeos lado a lado
        combined_output = np.hstack((display_hsv, display_bgr))
        
        # 7. Exibe o resultado
        # A janela terá 1920x540 (DISPLAY_WIDTH * 2, DISPLAY_HEIGHT)
        cv2.imshow("Comparacao de Metodos (HSV vs BGR-Split) - Pressione 'q' para sair", combined_output)

        # 8. Verifica se o usuário quer sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # --- Limpeza ---
    print("Encerrando...")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_comparison()