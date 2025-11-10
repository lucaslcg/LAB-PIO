# Como Interpretar o Relatório de Benchmark

O relatório gerado pelo benchmark foi projetado para fornecer uma visão completa e multifacetada do desempenho de cada método de detecção de cor. A análise correta desses dados é crucial para escolher o algoritmo mais adequado para a sua aplicação final.

O relatório é dividido em quatro blocos principais para cada método testado.

---

### 1. `[ Análise de Throughput ]` (Análise de Velocidade Geral)

Esta seção mede a "vazão" do sistema, ou seja, quantos quadros ele *realmente* consegue processar por segundo do início ao fim do teste.

-   **Quadros Processados:** O número total de frames analisados no teste.
-   **Tempo Total:** Quantos segundos o teste demorou para rodar.
-   **Throughput Real (FPS):** **(Métrica mais importante para velocidade)**. Este é o resultado de `Quadros Processados / Tempo Total`.
    -   **Interpretação:** Um valor **mais alto** é melhor. Ele indica que o método consegue processar mais imagens por segundo. Se seu objetivo é ter a imagem mais fluida possível, você vai preferir o método com maior FPS.

---

### 2. `[ Análise de Latência (Custo por Quadro) ]`

Esta seção detalha o "custo" de processar um único quadro, medido em milissegundos (ms). Latência é o inverso do throughput e mede a eficiência do algoritmo em uma única iteração.

-   **Média:** O tempo médio que o algoritmo levou para processar cada quadro.
    -   **Interpretação:** Um valor **mais baixo** é melhor. Significa que o algoritmo é mais rápido e eficiente em cada operação individual.
-   **Desvio Padrão:** Mede a consistência do tempo de processamento.
    -   **Interpretação:** Um valor **baixo** é ideal. Indica que o tempo de processamento é estável e previsível. Um valor alto significa que o desempenho varia muito, com alguns quadros sendo processados muito rápido e outros muito devagar.
-   **Pior / Melhor:** Mostra o tempo máximo e mínimo que levou para processar um quadro.
    -   **Interpretação:** O valor "Pior" é útil para entender o pior cenário de desempenho. Se esse número for muito alto, pode causar "engasgos" na aplicação.

---

### 3. `[ Análise de Uso de Recursos ]`

Esta seção mostra o impacto de cada método no hardware do seu Raspberry Pi.

-   **CPU Média / Pico:** O uso percentual médio e máximo do processador durante o teste.
    -   **Interpretação:** Valores **mais baixos** são melhores. Um método que usa menos CPU deixa mais recursos livres para outras tarefas no seu sistema operacional. O "Pico" mostra o estresse máximo que o método causou.
-   **Memória Média / Pico:** A quantidade de memória RAM (em Megabytes) que o script usou.
    -   **Interpretação:** Valores **mais baixos** são melhores. Um método mais eficiente em memória é crucial em sistemas com recursos limitados como o Raspberry Pi.

---

### 4. `[ Análise de Detecção ]`

Esta é a seção sobre a **precisão** e **confiabilidade** do algoritmo.

-   **Taxa Geral:** A porcentagem de quadros em que *qualquer* cor foi detectada com sucesso.
-   **Taxa por Cor (Preto, Verde, Vermelho):** A porcentagem de quadros em que cada cor específica foi detectada.
    -   **Interpretação:** Valores **mais altos** são melhores. Uma taxa de 95% para "Verde" significa que o algoritmo identificou corretamente o objeto verde em 95% do tempo. Esta é a métrica principal para decidir qual método é mais confiável.

---

### Conclusão Prática: Como Escolher o Melhor Método?

-   **Cenário 1: Você precisa da máxima velocidade e o ambiente de luz é controlado.**
    -   **O que procurar?** O método com o **maior Throughput (FPS)** e a **menor Latência Média**. Provavelmente será o **"Canal Puro"** ou **"Canal Dominante"**. Mesmo que a taxa de detecção seja um pouco menor, a velocidade pode ser mais importante.

-   **Cenário 2: Você precisa da máxima precisão, mesmo que seja um pouco mais lento.**
    -   **O que procurar?** O método com as **maiores Taxas de Detecção**. Provavelmente será o **"HSV"**. Ele pode ter um FPS menor e usar mais CPU, mas será mais confiável em diferentes condições de iluminação.

O objetivo do benchmark é te dar os dados para fazer essa escolha de forma informada, encontrando o equilíbrio perfeito entre **performance** e **precisão** para a sua aplicação.
