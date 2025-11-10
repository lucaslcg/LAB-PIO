# Benchmark de Detecção de Cor para Raspberry Pi

Este projeto é um benchmark científico projetado para analisar e comparar a performance e a precisão de três diferentes métodos de detecção de cor em tempo real no Raspberry Pi 5, utilizando as bibliotecas `OpenCV`, `NumPy` e `picamera2`.

## Descrição dos Métodos

O benchmark implementa e executa sequencialmente os três algoritmos a seguir, gerando um relatório detalhado para cada um:

### 1. Método HSV (Robusto)
- **Lógica:** Converte a imagem do espaço de cor padrão (BGR) para HSV (Hue, Saturation, Value). A detecção é feita criando uma máscara para um intervalo de matiz (Hue).
- **Vantagens:** Muito robusto a variações de iluminação, pois a informação de cor (H) é separada da intensidade de brilho (V). É considerado o padrão ouro para precisão.
- **Desvantagens:** A conversão `cvtColor` é computacionalmente cara, resultando em menor FPS.

### 2. Método Canal Dominante (Otimizado)
- **Lógica:** Opera diretamente nos canais BGR. Uma cor é considerada "dominante" se o valor do seu canal for significativamente maior que o dos outros dois (ex: `R > G` e `R > B`). Isso é calculado de forma eficiente usando operações de array NumPy (`R - max(G, B)`).
- **Vantagens:** Muito mais rápido que o método HSV, pois evita a conversão de cor. Ideal para ambientes com iluminação controlada.
- **Desvantagens:** Menos robusto que o HSV. Uma luz branca muito forte pode "estourar" os três canais, confundindo o algoritmo.

### 3. Método Canal Puro (Máxima Eficiência)
- **Lógica:** A abordagem mais simples e teoricamente mais rápida. Separa os canais de cor e aplica um limiar (threshold) diretamente no canal de interesse. Por exemplo, qualquer pixel no canal Vermelho com valor acima de um `THRESHOLD` é considerado "vermelho".
- **Vantagens:** Potencialmente o método mais rápido, pois envolve o mínimo de operações matemáticas. Funciona bem em cenários com fundo de cor neutra (como branco ou cinza), onde o canal da cor do objeto se destaca naturalmente.
- **Desvantagens:** O mais sensível dos três. Um reflexo de luz branca pode facilmente ter um valor alto em todos os canais, levando a falsos positivos.

## Como Executar no Raspberry Pi

A configuração no Raspberry Pi 5 (Debian Bookworm) requer passos específicos para garantir que a `picamera2` funcione corretamente dentro de um ambiente virtual.

### 1. Instale as Dependências do Sistema
```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-libcamera
```

### 2. Crie um Ambiente Virtual com Acesso aos Pacotes de Sistema
É **crucial** usar a flag `--system-site-packages` para que o venv possa acessar as bibliotecas do sistema que acabamos de instalar.
```bash
python3 -m venv .venv --system-site-packages
```

### 3. Ative o Ambiente Virtual
```bash
source .venv/bin/activate
```

### 4. Instale as Dependências Python
Com o ambiente ativado, instale as bibliotecas restantes via pip.
```bash
pip install -r requirements.txt
```

### 5. Execute o Benchmark
Agora, inicie a aplicação. O programa executará o teste para cada método, um após o outro. Pressione `s` na janela de visualização para iniciar cada teste.
```bash
python3 main.py
```
Ao final de cada teste, um relatório de desempenho será impresso no terminal. Pressione `Enter` no terminal para passar para o próximo método.

---

## Documentação Detalhada

Para uma análise mais aprofundada, consulte os seguintes documentos:

-   **[Como Interpretar o Relatório de Benchmark](./INTERPRETACAO_RELATORIO.md)**: Um guia completo sobre o que cada métrica significa e como usá-las para escolher o melhor método para sua necessidade.

-   **[Detalhamento do Fluxo de Processamento](./FLUXO_PROCESSAMENTO.md)**: Uma explicação passo a passo da lógica de cada algoritmo, incluindo as funções e bibliotecas utilizadas.
