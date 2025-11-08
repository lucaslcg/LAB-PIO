import cv2
import numpy as np
import time
from picamera2 import Picamera2

# --- 1. CONFIGURAÇÕES PRINCIPAIS ---

# Configurações do Benchmark
TOTAL_FRAMES_PER_TEST = 300  # Número de quadros para analisar por método

# Dimensões da Captura
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Fonte para o texto no HUD
FONT = cv2.FONT_HERSHEY_SIMPLEX

# Limite mínimo de área do contorno para evitar ruído
MIN_AREA = 1000

# --- 2. CALIBRAÇÃO DE COR (FIXA PARA O BENCHMARK) ---

HSV_RANGES = {
    'preto': ([0, 0, 0], [180, 255, 50]),
    'verde': ([35, 100, 100], [85, 255, 255]),
    'vermelho1': ([0, 100, 100], [10, 255, 255]),
    'vermelho2': ([170, 100, 100], [180, 255, 255])
}

BGR_RANGES = {
    'preto': ([0, 70], [0, 70], [0, 70]),
    'verde': ([0, 100], [120, 255], [0, 100]),
    'vermelho': ([0, 100], [0, 100], [120, 255])
}

SIGHT_COLORS = {
    'preto': (100, 100, 100),
    'verde': (0, 255, 0),
    'vermelho': (0, 0, 255)
}

# --- 3. FUNÇÕES DE PROCESSAMENTO E AUXILIARES ---

def find_and_draw_sights(frame, mask, name, color):
    """ Encontra o maior contorno na máscara, desenha a mira e retorna se o alvo foi encontrado """
    detected = False
    try:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) > MIN_AREA:
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
                cv2.putText(frame, name, (x, y - 10), FONT, 0.8, color, 2)
                detected = True
    except:
        pass
    return frame, detected

def draw_hud(frame, method_name, frame_count, proc_time_ms):
    """ Desenha um HUD simplificado para o benchmark """
    cv2.putText(frame, f"Metodo: {method_name}", (20, 40), FONT, 1.2, (255, 255, 0), 3)
    cv2.putText(frame, f"Frame: {frame_count} / {TOTAL_FRAMES_PER_TEST}", (20, 80), FONT, 1.2, (255, 255, 0), 3)
    cv2.putText(frame, f"Custo: {proc_time_ms:.2f} ms", (20, 120), FONT, 1.2, (255, 255, 0), 3)
    return frame

def print_benchmark_report(method_name, timings, detections):
    """ Imprime o relatório de performance para um método """
    total_frames = len(timings)
    detected_frames = sum(detections)
    detection_rate = (detected_frames / total_frames) * 100 if total_frames > 0 else 0

    avg_time = np.mean(timings) if timings else 0
    fps_potential = 1000.0 / avg_time if avg_time > 0 else float('inf')
    worst_time = max(timings) if timings else 0
    best_time = min(timings) if timings else 0

    print("\n--- Relatorio de Benchmark ---")
    print(f"Metodo: {method_name}")
    print("-" * 30)
    print(f"Total de Quadros Analisados: {total_frames}")
    print(f"Quadros com Alvos Detectados: {detected_frames}")
    print(f"Taxa de Deteccao: {detection_rate:.2f}%")
    print(f"Tempo Medio de Processamento: {avg_time:.2f} ms")
    print(f"FPS Medio (Potencial): {fps_potential:.1f}")
    print(f"Pior Tempo (max): {worst_time:.2f} ms")
    print(f"Melhor Tempo (min): {best_time:.2f} ms")
    print("-" * 30)

# --- 4. FUNÇÕES DE PROCESSAMENTO (OS DOIS MÉTODOS) ---

def process_hsv(frame):
    """ Método 1: Tradicional com BGR2HSV """
    t_start = cv2.getTickCount()

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask_preto = cv2.inRange(hsv, np.array(HSV_RANGES['preto'][0]), np.array(HSV_RANGES['preto'][1]))
    mask_verde = cv2.inRange(hsv, np.array(HSV_RANGES['verde'][0]), np.array(HSV_RANGES['verde'][1]))
    mask_vermelho = cv2.bitwise_or(cv2.inRange(hsv, np.array(HSV_RANGES['vermelho1'][0]), np.array(HSV_RANGES['vermelho1'][1])),
                                 cv2.inRange(hsv, np.array(HSV_RANGES['vermelho2'][0]), np.array(HSV_RANGES['vermelho2'][1])))

    # Combina todas as máscaras para verificar a detecção de qualquer alvo
    combined_mask = cv2.bitwise_or(mask_preto, cv2.bitwise_or(mask_verde, mask_vermelho))

    frame, detected_p = find_and_draw_sights(frame, mask_preto, "PRETO", SIGHT_COLORS['preto'])
    frame, detected_v = find_and_draw_sights(frame, mask_verde, "VERDE", SIGHT_COLORS['verde'])
    frame, detected_r = find_and_draw_sights(frame, mask_vermelho, "VERMELHO", SIGHT_COLORS['vermelho'])

    proc_time = ((cv2.getTickCount() - t_start) / cv2.getTickFrequency()) * 1000
    return frame, proc_time, any([detected_p, detected_v, detected_r])

def process_bgr_split(frame):
    """ Método 2: Manipulação de canais BGR """
    t_start = cv2.getTickCount()

    b, g, r = cv2.split(frame)

    r_b, r_g, r_r = BGR_RANGES['preto']
    mask_preto = cv2.bitwise_and(cv2.inRange(b, r_b[0], r_b[1]), cv2.bitwise_and(cv2.inRange(g, r_g[0], r_g[1]), cv2.inRange(r, r_r[0], r_r[1])))

    r_b, r_g, r_r = BGR_RANGES['verde']
    mask_verde = cv2.bitwise_and(cv2.inRange(b, r_b[0], r_b[1]), cv2.bitwise_and(cv2.inRange(g, r_g[0], r_g[1]), cv2.inRange(r, r_r[0], r_r[1])))

    r_b, r_g, r_r = BGR_RANGES['vermelho']
    mask_vermelho = cv2.bitwise_and(cv2.inRange(b, r_b[0], r_b[1]), cv2.bitwise_and(cv2.inRange(g, r_g[0], r_g[1]), cv2.inRange(r, r_r[0], r_r[1])))

    frame, detected_p = find_and_draw_sights(frame, mask_preto, "PRETO", SIGHT_COLORS['preto'])
    frame, detected_v = find_and_draw_sights(frame, mask_verde, "VERDE", SIGHT_COLORS['verde'])
    frame, detected_r = find_and_draw_sights(frame, mask_vermelho, "VERMELHO", SIGHT_COLORS['vermelho'])

    proc_time = ((cv2.getTickCount() - t_start) / cv2.getTickFrequency()) * 1000
    return frame, proc_time, any([detected_p, detected_v, detected_r])

# --- 5. FUNÇÃO PRINCIPAL DE BENCHMARK ---
def run_benchmark():
    # Mapeia nomes de método para suas funções
    methods = {
        "HSV (Tradicional)": process_hsv,
        "BGR-Split": process_bgr_split
    }

    print("Iniciando a câmera com Picamera2...")
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"format": "BGR888", "size": (FRAME_WIDTH, FRAME_HEIGHT)})
    picam2.configure(config)
    picam2.start()
    time.sleep(1.0)

    for method_name, process_function in methods.items():
        print(f"\nIniciando benchmark para o metodo: {method_name}")
        print(f"O teste sera executado por {TOTAL_FRAMES_PER_TEST} quadros.")
        print("Pressione 's' na janela para iniciar o teste...")

        timings = []
        detections = []

        frame_count = 0
        test_started = False

        while frame_count < TOTAL_FRAMES_PER_TEST:
            # Captura o frame (formato RGB)
            frame_rgb = picam2.capture_array()
            if frame_rgb is None: continue

            # Converte de RGB para BGR usando a função robusta do OpenCV
            frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            if not test_started:
                # Mostra uma tela de espera até o usuário pressionar 's'
                startup_text = "Pressione 's' para iniciar..."
                # Garante que o frame seja contíguo na memória antes de desenhar
                frame_contiguous = np.ascontiguousarray(frame)
                cv2.putText(frame_contiguous, startup_text, (50, FRAME_HEIGHT // 2), FONT, 1.5, (0, 255, 255), 4)
                cv2.imshow(f"Benchmark - {method_name}", frame_contiguous)
                if cv2.waitKey(1) & 0xFF == ord('s'):
                    test_started = True
                continue

            # Executa o processamento
            processed_frame, proc_time, detected = process_function(frame.copy())

            # Coleta os dados
            timings.append(proc_time)
            detections.append(detected)
            frame_count += 1

            # Mostra a saída visual com o HUD
            display_frame = draw_hud(processed_frame, method_name, frame_count, proc_time)
            cv2.imshow(f"Benchmark - {method_name}", display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Teste interrompido pelo usuario.")
                break

        # Gera o relatório para o método atual
        print_benchmark_report(method_name, timings, detections)
        cv2.destroyAllWindows()

        # Pausa antes do próximo teste
        if method_name != list(methods.keys())[-1]:
            print("\nPressione qualquer tecla no terminal para iniciar o proximo teste...")
            input()

    print("\nBenchmark concluido.")
    picam2.stop()

if __name__ == "__main__":
    run_benchmark()
