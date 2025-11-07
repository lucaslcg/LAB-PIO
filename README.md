# LAB-PIO
Laboratório de processamento de imagem otimizado - experimento pessoal sobre formas mais eficientes de processar imagens com o OpenCV para hardwares de baixo poder de processamento.

## Descrição

Este projeto compara dois métodos de detecção de cores em tempo real usando OpenCV:

1.  **Método 1 (BGR2HSV):** A abordagem tradicional e mais robusta, que converte o espaço de cores de BGR para HSV para uma melhor segmentação de cores.
2.  **Método 2 (BGR-Split):** Uma abordagem alternativa que opera diretamente nos canais BGR. É potencialmente mais rápida, mas muito mais sensível a variações de iluminação.

O objetivo é analisar a performance de cada método em hardwares com recursos limitados, como o Raspberry Pi.

## Como Executar

Siga os passos abaixo para configurar e executar o projeto em um ambiente virtual.

### 1. Crie um Ambiente Virtual (venv)

Com o Python 3 instalado, crie um ambiente virtual para isolar as dependências do projeto.

```bash
python3 -m venv .venv
```

### 2. Ative o Ambiente Virtual

**No Linux ou macOS:**
```bash
source .venv/bin/activate
```

**No Windows:**
```bash
.venv\Scripts\activate
```

### 3. Instale as Dependências

Com o ambiente virtual ativado, instale as bibliotecas necessárias a partir do arquivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 4. Execute o Programa

Agora, você pode iniciar a aplicação.

```bash
python3 main.py
```

Pressione a tecla 'q' na janela do OpenCV para encerrar a execução.
