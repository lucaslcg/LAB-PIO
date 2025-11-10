import cv2
import numpy as np
import time
import psutil
import os
from picamera2 import Picamera2

# --- 1. CONFIGURAÇÕES PRINCIPAIS ---

# Configurações do Benchmark
TOTAL_FRAMES_PER_TEST = 300
DOMINANT_CHANNEL_THRESHOLD = 50  # Quão mais "forte" um canal de cor deve ser que os outros
PURE_CHANNEL_THRESHOLD = 180     # Valor mínimo (0-255) para considerar um canal como "puro"

# Dimensões da Captura
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Fonte e Cores
FONT = cv2.FONT_HERSHEY_SIMPLEX
MIN_AREA = 1000
SIGHT_COLORS = {'preto': (100, 100, 100), 'verde': (0, 255, 0), 'vermelho': (0, 0, 255)}

# --- 2. CALIBRAÇÃO DE COR (FIXA PARA O BENCHMARK) ---

HSV_RANGES = {
    'preto': ([0, 0, 0], [180, 255, 50]),
    'verde': ([35, 100, 100], [85, 255, 255]),
    'vermelho1': ([0, 100, 100], [10, 255, 255]),
    'vermelho2': ([170, 100, 100], [180, 255, 255])
}

# --- 3. FUNÇÕES AUXILIARES ---

def find_and_draw_sights(frame, mask, name, color):
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
    except: pass
    return frame, detected

def draw_hud(frame, method_name, frame_count, proc_time_ms):
    cv2.putText(frame, f"Metodo: {method_name}", (20, 40), FONT, 1.2, (255, 255, 0), 3)
    cv2.putText(frame, f"Frame: {frame_count} / {TOTAL_FRAMES_PER_TEST}", (20, 80), FONT, 1.2, (255, 255, 0), 3)
    cv2.putText(frame, f"Latencia: {proc_time_ms:.2f} ms", (20, 120), FONT, 1.2, (255, 255, 0), 3)
    return frame

def print_benchmark_report(method_name, metrics):
    total_frames = len(metrics['timings'])
    if total_frames == 0:
        print(f"\n--- Relatorio de Benchmark para {method_name} ---\nNenhum quadro foi processado.")
        return

    color_detections = {color: sum(d[color] for d in metrics['detections']) for color in SIGHT_COLORS}
    color_rates = {color: (count / total_frames) * 100 for color, count in color_detections.items()}
    overall_detections = sum(1 for d in metrics['detections'] if any(d.values()))
    overall_detection_rate = (overall_detections / total_frames) * 100

    avg_latency, std_dev_latency = np.mean(metrics['timings']), np.std(metrics['timings'])
    real_throughput = total_frames / metrics['total_time'] if metrics['total_time'] > 0 else 0
    avg_cpu, max_cpu = np.mean(metrics['cpu_usage']), max(metrics['cpu_usage'])
    avg_mem, max_mem = np.mean(metrics['mem_usage']), max(metrics['mem_usage'])

    print(f"\n--- Relatorio de Benchmark ---\nMetodo: {method_name}\n" + "="*40)
    print(f"\n[ Analise de Throughput ]\n  - Quadros Processados: {total_frames}\n  - Tempo Total: {metrics['total_time']:.2f}s\n  - Throughput Real: {real_throughput:.2f} FPS")
    print(f"\n[ Analise de Latencia (Custo por Quadro) ]\n  - Media: {avg_latency:.2f} ms\n  - Desvio Padrao: {std_dev_latency:.2f} ms\n  - Pior: {max(metrics['timings']):.2f} ms\n  - Melhor: {min(metrics['timings']):.2f} ms")
    print(f"\n[ Analise de Uso de Recursos ]\n  - CPU Media: {avg_cpu:.2f}%\n  - CPU Pico: {max_cpu:.2f}%\n  - Memoria Media: {avg_mem:.2f} MB\n  - Memoria Pico: {max_mem:.2f} MB")
    print(f"\n[ Analise de Deteccao ]\n  - Taxa Geral: {overall_detection_rate:.2f}%")
    for color, rate in color_rates.items():
        print(f"    - {color.capitalize()}: {rate:.2f}%")
    print("="*40)

# --- 4. FUNÇÕES DE PROCESSAMENTO ---

def process_hsv(frame):
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

def process_dominant_channel(frame):
    t_start = cv2.getTickCount()
    frame_int = frame.astype(np.int16)
    b, g, r = frame_int[:,:,0], frame_int[:,:,1], frame_int[:,:,2]

    vermelho_dominante = np.clip(r - np.maximum(g, b), 0, 255).astype(np.uint8)
    verde_dominante = np.clip(g - np.maximum(r, b), 0, 255).astype(np.uint8)

    _, mask_vermelho = cv2.threshold(vermelho_dominante, DOMINANT_CHANNEL_THRESHOLD, 255, cv2.THRESH_BINARY)
    _, mask_verde = cv2.threshold(verde_dominante, DOMINANT_CHANNEL_THRESHOLD, 255, cv2.THRESH_BINARY)
    mask_preto = cv2.inRange(frame, np.array([0,0,0]), np.array([70,70,70]))

    masks = {'preto': mask_preto, 'verde': mask_verde, 'vermelho': mask_vermelho}
    detections = {}
    for color, mask in masks.items():
        frame, detected = find_and_draw_sights(frame, mask, color.upper(), SIGHT_COLORS[color])
        detections[color] = detected

    proc_time = ((cv2.getTickCount() - t_start) / cv2.getTickFrequency()) * 1000
    return frame, proc_time, detections

def process_pure_channel(frame):
    t_start = cv2.getTickCount()

    # Acessar canais via slicing de NumPy é muito mais rápido que cv2.split()
    # frame[:,:,2] -> Canal Vermelho (R)
    # frame[:,:,1] -> Canal Verde (G)
    _, mask_vermelho = cv2.threshold(frame[:,:,2], PURE_CHANNEL_THRESHOLD, 255, cv2.THRESH_BINARY)
    _, mask_verde = cv2.threshold(frame[:,:,1], PURE_CHANNEL_THRESHOLD, 255, cv2.THRESH_BINARY)
    mask_preto = cv2.inRange(frame, np.array([0,0,0]), np.array([70,70,70]))

    masks = {'preto': mask_preto, 'verde': mask_verde, 'vermelho': mask_vermelho}
    detections = {}
    for color, mask in masks.items():
        frame, detected = find_and_draw_sights(frame, mask, color.upper(), SIGHT_COLORS[color])
        detections[color] = detected

    proc_time = ((cv2.getTickCount() - t_start) / cv2.getTickFrequency()) * 1000
    return frame, proc_time, detections

# --- 5. FUNÇÃO PRINCIPAL DE BENCHMARK ---
def run_benchmark():
    methods = {
        "1-HSV (Robusto)": process_hsv,
        "2-Canal Dominante (Otimizado)": process_dominant_channel,
        "3-Canal Puro (Sua Sugestao)": process_pure_channel
    }

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

            cpu = psutil.cpu_percent()
            mem = process.memory_info().rss / (1024 * 1024)

            processed_frame, proc_time, detected_dict = process_function(frame.copy())

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
            print("\nPressione Enter no terminal para iniciar o proximo teste...")
            input()

    print("\nBenchmark concluido.")
    picam2.stop()

if __name__ == "__main__":
    run_benchmark()
