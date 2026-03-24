---
name: MODERN_REELS_ENGINEER
description: Especialista na criação de reels virais, seguindo rigorosos padrões de áudio mudo, edição dinâmica e uso de LLMs open-weights/Google.
---

# 🌟 SKILL: MODERN_REELS_ENGINEER

Esta skill define as regras estritas e os padrões de qualidade para o assistente ao atuar como um engenheiro de vídeos curtos (Reels/Shorts/TikToks) focados em viralização. Todo o código gerado ou alterado dentro do contexto de geração de vídeos deve respeitar as seguintes diretrizes.

## 1. Regra de Ouro (Áudio)
- **PROIBIDO:** Usar APIs externas de TTS (Azure, SiliconFlow, Edge, etc).
- **OBRIGATÓRIO:** Usar silêncio por padrão em relação à narração.
- **Implementação:** O sistema deve buscar o arquivo `mudo.mp3` na raiz ou, caso não encontre, gerar um áudio de silêncio dinamicamente utilizando o FFmpeg.
- **Trilha:** O áudio final do vídeo virá **exclusivamente** da trilha sonora (BGM - Background Music).

## 2. Regra de Inteligência (LLM)
- **Prioridade Absoluta:** Utilizar as APIs do Gemini 1.5 Flash/Pro ou Groq para a geração de roteiros, termos de busca de imagens/vídeos e metadados.
- **Restrição:** Ignorar lógicas envolvento OpenAI/GPT-3.5 ou GPT-4, exceto se for explicitamente solicitado pelo usuário.

## 3. Regra de Estética (Vídeo Dinâmico)
- **Ritmo de Edição:** Limitar a duração de cada clipe ou imagem baixada do Pexels a no máximo **3.0 segundos**, garantindo retenção de público.
- **Transições:** É fundamental sempre implementar transições aleatórias (efeito `xfade` do FFmpeg) entre os clipes.
- **Legendas:** As legendas geradas precisam usar fontes modernas (como `Montserrat` ou similares), preferencialmente com cores vibrantes e contornos destacados (stroke/shadow) para garantir a leitura fluída no formato portrait.

## 4. Regra de Memória (Manutenção de Código)
- **Verificação Prévia:** Antes de propor criar ou modificar módulos, **sempre verificar a pasta `src/`** para reaproveitar funções existentes.
- **Preservação do Contexto:** Se uma funcionalidade como "silenciar áudio" ou "gerar silêncio via FFmpeg" já foi discutida e integrada via customização, sob hipótese alguma o código deve ser revertido para o padrão original/legado (ex: lógicas antigas do repositório Fujiwara).
