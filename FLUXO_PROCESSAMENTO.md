# Detalhamento do Fluxo de Processamento de Imagem

Este documento descreve o fluxo de processamento passo a passo para cada um dos três métodos de detecção de cor implementados no benchmark, incluindo as funções e bibliotecas utilizadas.

---

### Método 1: `process_hsv` (Robusto)

Este método é o mais tradicional e confiável, pois o espaço de cor **HSV (Hue, Saturation, Value)** isola a informação de cor (Hue) da de brilho (Value), tornando-o menos sensível a variações de iluminação.

**Fluxo de Processamento:**

1.  **Conversão de Espaço de Cor**: A imagem, recebida no formato BGR (Azul, Verde, Vermelho), é convertida para o formato HSV.
    -   **Função:** `cv2.cvtColor()`
    -   **Biblioteca:** `cv2` (OpenCV)
    -   **No código:** `hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)`

2.  **Criação de Máscaras de Cor**: Para cada cor, é criada uma "máscara" binária (preto e branco) onde pixels brancos representam a cor desejada.
    -   **Função:** `cv2.inRange()`
    -   **Biblioteca:** `cv2` (OpenCV)
    -   **Para a cor Vermelha:** Duas máscaras são criadas para abranger as duas extremidades do espectro de matiz e são unidas com uma operação `OR`.
        -   **Função de União:** `cv2.bitwise_or()`
        -   **Biblioteca:** `cv2` (OpenCV)

3.  **Encontrar Contornos**: O algoritmo busca por todas as formas (contornos) brancas contínuas na máscara.
    -   **Função:** `cv2.findContours()`
    -   **Biblioteca:** `cv2` (OpenCV)

4.  **Análise e Desenho**: O maior contorno encontrado (se atender a uma área mínima) é identificado como o objeto. Um retângulo e um texto são desenhados sobre ele na imagem original.
    -   **Medir Área:** `cv2.contourArea()`
    -   **Obter Retângulo:** `cv2.boundingRect()`
    -   **Desenhar Retângulo:** `cv2.rectangle()`
    -   **Escrever Texto:** `cv2.putText()`
    -   **Biblioteca:** Todas da `cv2` (OpenCV).

---

### Método 2: `process_dominant_channel` (Otimizado)

Este método evita a custosa conversão para HSV, operando diretamente nos canais BGR com matemática de arrays para encontrar a cor "dominante" em cada pixel.

**Fluxo de Processamento:**

1.  **Separação de Canais (Eficiente)**: Os canais B, G e R são separados usando fatiamento de array, que é extremamente rápido.
    -   **Função:** Fatiamento de array (`frame[:,:,0]`).
    -   **Biblioteca:** `numpy`

2.  **Cálculo de "Dominância"**: Para cada pixel, calcula-se o quão mais "forte" um canal de cor é em relação aos outros dois.
    -   **Exemplo para Vermelho:** `r - np.maximum(g, b)`.
    -   **Função:** `np.maximum()`
    -   **Biblioteca:** `numpy`

3.  **Normalização e Limiar**: O resultado é normalizado para o intervalo 0-255 e convertido em uma máscara binária aplicando um limiar (`threshold`).
    -   **Funções:** `np.clip()`, `cv2.threshold()`
    -   **Bibliotecas:** `numpy`, `cv2` (OpenCV)

4.  **Encontrar Contornos e Desenhar**: O processo final é idêntico ao do método HSV: `findContours`, `contourArea`, `boundingRect`, `rectangle`, `putText`.

---

### Método 3: `process_pure_channel` (Máxima Eficiência)

Esta é a abordagem mais direta, ideal para cenários de alto contraste e fundo neutro.

**Fluxo de Processamento:**

1.  **Separação de Canais (Eficiente)**: Assim como no método anterior, os canais B, G e R são obtidos via fatiamento de array NumPy.
    -   **Função:** Fatiamento de array (`frame[:,:,2]` para o canal Vermelho).
    -   **Biblioteca:** `numpy`

2.  **Criação de Máscara por Limiar (Threshold)**: Uma máscara binária é criada aplicando diretamente um limiar no canal de interesse. Qualquer pixel no canal com valor acima do `PURE_CHANNEL_THRESHOLD` se torna branco.
    -   **Função:** `cv2.threshold()`
    -   **Biblioteca:** `cv2` (OpenCV)
    -   **Para a cor Preta:** A detecção de preto ainda utiliza `cv2.inRange`, pois é a forma mais eficaz de definir um "teto" para todos os canais.

3.  **Encontrar Contornos e Desenhar**: O processo final é novamente idêntico aos outros métodos: `findContours`, `contourArea`, `boundingRect`, `rectangle`, `putText`.

Em resumo, a grande diferença entre os métodos está em **como a máscara de cor é criada**: o método **HSV** usa uma transformação de cor robusta; o **Canal Dominante** usa álgebra de arrays `numpy` para uma abordagem rápida; e o **Canal Puro** usa a operação `threshold`, a mais simples e rápida de todas.
