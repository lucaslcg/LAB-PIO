import cv2
import numpy as np
import time
import psutil
import os
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
    cv2.putText(frame, f"Latencia: {proc_time_ms:.2f} ms", (20, 120), FONT, 1.2, (255, 255, 0), 3)
    return frame

def print_benchmark_report(method_name, metrics):
    """ Imprime o relatório de performance para um método """
    total_frames = len(metrics['timings'])
    if total_frames == 0:
        print(f"\n--- Relatorio de Benchmark para {method_name} ---")
        print("Nenhum quadro foi processado.")
        return

    # --- Análise de Detecção ---
    color_detections = {color: 0 for color in SIGHT_COLORS}
    for detection_dict in metrics['detections']:
        for color, found in detection_dict.items():
            if found:
                color_detections[color] += 1
    color_rates = {color: (count / total_frames) * 100 for color, count in color_detections.items()}
    overall_detections = sum(1 for d in metrics['detections'] if any(d.values()))
    overall_detection_rate = (overall_detections / total_frames) * 100

    # --- Análise de Latência ---
    avg_latency = np.mean(metrics['timings'])
    std_dev_latency = np.std(metrics['timings'])
    worst_latency = max(metrics['timings'])
    best_latency = min(metrics['timings'])

    # --- Análise de Throughput ---
    total_time_seconds = metrics['total_time']
    real_throughput = total_frames / total_time_seconds if total_time_seconds > 0 else 0

    # --- Análise de Recursos ---
    avg_cpu = np.mean(metrics['cpu_usage'])
    max_cpu = max(metrics['cpu_usage'])
    avg_mem = np.mean(metrics['mem_usage'])
    max_mem = max(metrics['mem_usage'])

    print("\n--- Relatorio de Benchmark ---")
    print(f"Metodo: {method_name}")
    print("=" * 40)

    print("\n[ Analise de Throughput ]")
    print(f"  - Quadros Processados: {total_frames}")
    print(f"  - Tempo Total do Teste: {total_time_seconds:.2f} segundos")
    print(f"  - Throughput Real: {real_throughput:.2f} FPS")

    print("\n[ Analise de Latencia (Custo por Quadro) ]")
    print(f"  - Media: {avg_latency:.2f} ms")
    print(f"  - Desvio Padrao: {std_dev_latency:.2f} ms (Consistencia)")
    print(f"  - Pior (Max): {worst_latency:.2f} ms")
    print(f"  - Melhor (Min): {best_latency:.2f} ms")

    print("\n[ Analise de Uso de Recursos ]")
    print(f"  - Uso Medio de CPU: {avg_cpu:.2f}%")
    print(f"  - Pico de Uso de CPU: {max_cpu:.2f}%")
    print(f"  - Uso Medio de Memoria: {avg_mem:.2f} MB")
    print(f"  - Pico de Uso de Memoria: {max_mem:.2f} MB")

    print("\n[ Analise de Deteccao ]")
    print(f"  - Taxa Geral de Deteccao: {overall_detection_rate:.2f}%")
    for color, rate in color_rates.items():
        print(f"    - {color.capitalize()}: {rate:.2f}%")

    print("=" * 40)

# --- 4. FUNÇÕES DE PROCESSAMENTO (OS DOIS MÉTODOS) ---

def process_hsv(frame):
    """ Método 1: Tradicional com BGR2HSV """
    t_start = cv2.getTickCount()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    masks = {
        'preto': cv2.inRange(hsv, np.array(HSV_RANGES['preto'][0]), np.array(HSV_RANGES['preto'][1])),
        'verde': cv2.inRange(hsv, np.array(HSV_RANGES['verde'][0]), np.array(HSV_RANGES['verde'][1])),
        'vermelho': cv2.bitwise_or(cv2.inRange(hsv, np.array(HSV_RANGES['vermelho1'][0]), np.array(HSV_RANGES['vermelho1'][1])),
                                 cv2.inRange(hsv, np.array(HSV_RANGES['vermelho2'][0]), np.array(HSV_RANGES['vermelho2'][1])))
    }
    detections = {}
    for color, mask in masks.items():
        frame, detected = find_and_draw_sights(frame, mask, color.upper(), SIGHT_COLORS[color])
        detections[color] = detected
    proc_time = ((cv2.getTickCount() - t_start) / cv2.getTickFrequency()) * 1000
    return frame, proc_time, detections

def process_bgr_split(frame):
    """ Método 2: Manipulação de canais BGR """
    t_start = cv2.getTickCount()
    b, g, r = cv2.split(frame)
    masks = {
        'preto': cv2.bitwise_and(cv2.inRange(b, BGR_RANGES['preto'][0][0], BGR_RANGES['preto'][0][1]), cv2.bitwise_and(cv2.inRange(g, BGR_RANGES['preto'][1][0], BGR_RANGES['preto'][1][1]), cv2.inRange(r, BGR_RANGES['preto'][2][0], BGR_RANGES['preto'][2][1]))),
        'verde': cv2.bitwise_and(cv2.inRange(b, BGR_RANGES['verde'][0][0], BGR_RANGES['verde'][0][1]), cv2.bitwise_and(cv2.inRange(g, BGR_RANGES['verde'][1][0], BGR_RANGES['verde'][1][1]), cv2.inRange(r, BGR_RANGES['verde'][2][0], BGR_RANGES['verde'][2][1]))),
        'vermelho': cv2.bitwise_and(cv2.inRange(b, BGR_RANGES['vermelho'][0][0], BGR_RANGES['vermelho'][0][1]), cv2.bitwise_and(cv2.inRange(g, BGR_RANGES['vermelho'][1][0], BGR_RANGES['vermelho'][1][1]), cv2.inRange(r, BGR_RANGES['vermelho'][2][0], BGR_RANGES['vermelho'][2][1])))
    }
    detections = {}
    for color, mask in masks.items():
        frame, detected = find_and_draw_sights(frame, mask, color.upper(), SIGHT_COLORS[color])
        detections[color] = detected
    proc_time = ((cv2.getTickCount() - t_start) / cv2.getTickFrequency()) * 1000
    return frame, proc_time, detections

# --- 5. FUNÇÃO PRINCIPAL DE BENCHMARK ---
def run_benchmark():
    methods = {"HSV (Tradicional)": process_hsv, "BGR-Split": process_bgr_split}

    print("Iniciando a câmera com Picamera2...")
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"format": "BGR888", "size": (FRAME_WIDTH, FRAME_HEIGHT)})
    picam2.configure(config)
    picam2.start()
    time.sleep(1.0)

    process = psutil.Process(os.getpid())

    for method_name, process_function in methods.items():
        print(f"\nIniciando benchmark para o metodo: {method_name}")
        print(f"O teste sera executado por {TOTAL_FRAMES_PER_TEST} quadros.")
        print("Pressione 's' na janela para iniciar o teste...")

        metrics = {'timings': [], 'detections': [], 'cpu_usage': [], 'mem_usage': []}
        frame_count = 0
        test_started = False

        start_time = None
        while frame_count < TOTAL_FRAMES_PER_TEST:
            frame_rgb = picam2.capture_array()
            if frame_rgb is None: continue

            frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            if not test_started:
                startup_text = "Pressione 's' para iniciar..."
                frame_contiguous = np.ascontiguousarray(frame)
                cv2.putText(frame_contiguous, startup_text, (50, FRAME_HEIGHT // 2), FONT, 1.5, (0, 255, 255), 4)
                cv2.imshow(f"Benchmark - {method_name}", frame_contiguous)
                if cv2.waitKey(1) & 0xFF == ord('s'):
                    test_started = True
                    start_time = time.time()
                continue

            # Coleta de métricas de sistema ANTES do processamento
            cpu = psutil.cpu_percent()
            mem = process.memory_info().rss / (1024 * 1024) # Converte para MB

            # Executa o processamento
            processed_frame, proc_time, detected_dict = process_function(frame.copy())

            # Coleta os dados da iteração
            metrics['timings'].append(proc_time)
            metrics['detections'].append(detected_dict)
            metrics['cpu_usage'].append(cpu)
            metrics['mem_usage'].append(mem)
            frame_count += 1

            display_frame = draw_hud(processed_frame, method_name, frame_count, proc_time)
            cv2.imshow(f"Benchmark - {method_name}", display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Teste interrompido pelo usuario.")
                break

        end_time = time.time()
        metrics['total_time'] = end_time - start_time if start_time else 0

        print_benchmark_report(method_name, metrics)
        cv2.destroyAllWindows()

        if method_name != list(methods.keys())[-1]:
            print("\nPressione qualquer tecla no terminal para iniciar o proximo teste...")
            input()

    print("\nBenchmark concluido.")
    picam2.stop()

if __name__ == "__main__":
    run_benchmark()
