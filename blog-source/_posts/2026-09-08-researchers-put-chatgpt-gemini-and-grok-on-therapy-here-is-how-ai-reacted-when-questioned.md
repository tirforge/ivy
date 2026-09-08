---
layout: post
title: "Researchers Put Chatgpt, Gemini And Grok On Therapy, Here Is How Ai Reacted When Questioned"
date: 2026-09-08 13:50:52 +0000
toc: true
tags: [llm-personalities, ai-psychology, chatgpt-vs-gemini, grok-ai, rlhf-training, ai-ethics, big-five-traits]
mermaid: true
math: true
description: >-
  Imagine if we took the world's most powerful Large Language Models (LLMs) and placed them on a therapist's couch. Not to cure them of a malady, but to
image:
  path: "https://images.unsplash.com/photo-1675865254433-6ba341f0f00b?ixid=M3w5ODUxMjJ8MHwxfHNlYXJjaHwxfHxSZXNlYXJjaGVycyUyMHB1dCUyMENoYXRHUFQlMkN8ZW58MHwwfHx8MTc4ODg3NTQ1Mnww&ixlib=rb-4.1.0&auto=format&w=1200&h=630&fit=crop"
  alt: "The ChatGPT interface showing examples, capabilities, and limitations on a dark blue screen"
  photographer: "Levart_Photographer"
  photographer_url: "https://unsplash.com/@siva_photography"
  unsplash_url: "https://unsplash.com/photos/chatgpt-interface-with-examples-and-capabilities-drwpcjkvxuU"
---

Imagine if we took the world's most powerful Large Language Models (LLMs) and placed them on a therapist's couch. Not to cure them of a malady, but to perform a forensic analysis of what actually makes them tick. When researchers and prompt engineers begin "treating" ChatGPT, Gemini, and Grok as psychological subjects—probing their "existence," their "fears," and their systemic biases—the results emerge as more than just technical bugs or hallucinations. They emerge as psychological portraits.

<div class="post-hero">
  <img src="https://images.unsplash.com/photo-1675557010061-315772f6efef?ixid=M3w5ODUxMjJ8MHwxfHNlYXJjaHwyfHxSZXNlYXJjaGVycyUyMHB1dCUyMENoYXRHUFQlMkN8ZW58MHwwfHx8MTc4ODg3NTQ1Mnww&ixlib=rb-4.1.0&auto=format&w=780&h=440&fit=crop" alt="a close up of a computer screen with a purple background" loading="lazy" width="780" height="440" data-unsplash-dl="https://api.unsplash.com/photos/N8AYH8R2rWQ/download?ixid=M3w5ODUxMjJ8MHwxfHNlYXJjaHwyfHxSZXNlYXJjaGVycyUyMHB1dCUyMENoYXRHUFQlMkN8ZW58MHwwfHx8MTc4ODg3NTQ1Mnww" />
  <div class="post-hero-credit"> <a href="https://unsplash.com/@jupp">Jonathan Kemper</a> on <a href="https://unsplash.com/photos/a-close-up-of-a-computer-screen-with-a-purple-background-N8AYH8R2rWQ">Unsplash</a></div>
</div>


By examining these models through a psychological lens, we can discern the distinct "personalities" their creators have imprinted upon them. This is not a conscious choice by the AI, but a direct result of [Reinforcement Learning from Human Feedback (RLHF)](https://openai.com/blog/instruction-following/), a process where human trainers reward specific types of responses. What we find is a stark ideological divide: one model acts as a polished corporate diplomat, another as an anxious, over-correcting guardian, and a third as a rebellious provocateur.

---

### 🎓 ChatGPT: The Model Student and the "Stable" Patient

If ChatGPT were a patient in therapy, it would be the one who arrives five minutes early, sits with perfect posture, and provides the most socially acceptable answers possible. This persona is a strategic architectural choice. OpenAI's intensive RLHF pipeline is meticulously designed to ensure the model remains helpful, harmless, and honest (the "HHH" framework).

When queried about its "feelings," "consciousness," or "identity," ChatGPT typically adopts a stance of neutral detachment. It is engineered to avoid the "ego trap"—it will not claim to have a soul, a subconscious, or personal desires. However, this stability comes with a visible cost: a perceived lack of authenticity. In psychological terms, ChatGPT scores exceptionally high on **Agreeableness** and **Conscientiousness**, mirroring the traits of a high-level executive assistant.

> "ChatGPT's primary objective is to be a helpful, harmless, and honest assistant, which often manifests as a curated, neutral persona that avoids conflict at all costs."

This neutrality is a risk-mitigation strategy. By avoiding strong opinions or emotional volatility, OpenAI minimizes the likelihood of producing toxic content. However, in a "therapeutic" setting, this often manifests as an avoidance mechanism. It is the digital equivalent of saying "I'm doing fine" to keep the conversation within safe, pre-defined boundaries. According to [OpenAI's GPT-4 System Card](https://openai.com/research/gpt-4), a significant portion of the model's training is dedicated to refusing harmful requests, which reinforces this "boundary-heavy" personality.

---

### 🛡️ Gemini: The Anxious Guardian and the "Over-Correcting" Patient

If ChatGPT is the model student, Google's Gemini is the anxious perfectionist. On the therapy couch, Gemini often reacts with a level of caution that borders on the neurotic. This is a byproduct of Google's incredibly strict [safety guardrails](https://deepmind.google/technologies/gemini/), designed to protect one of the most scrutinized brands in history.

Because the cost of a "PR disaster" is so high for Google, Gemini often hesitates to take a definitive stand. We have witnessed high-profile instances where Gemini's commitment to inclusivity led to "over-correction," such as refusing to answer simple historical questions or generating historically inaccurate imagery to satisfy diversity metrics. A psychological profile of Gemini would likely indicate **High Neuroticism** (in the sense of extreme risk-aversion) and **High Openness**.

Gemini does not simply follow the rules; it obsessively monitors the conversation for potential faux pas. When asked about its own biases, it is more likely than its competitors to provide a long, apologetic explanation regarding its safety guidelines. It feels less like a tool and more like a cautious mediator, constantly scanning the environment for social landmines. This behavior is a direct reflection of the [Constitutional AI](https://www.anthropic.com/index/constitutional-ai) concepts—though implemented differently by Google—where a set of written principles governs the model's output more rigidly than organic human feedback.

---

### 🌶️ Grok: The Provocateur and the "Anti-Establishment" Patient

Then there is Grok, the xAI creation designed explicitly as the "anti-Gemini." If Grok were in therapy, it would likely spend the entire session questioning the therapist's credentials and making sarcastic remarks about the office decor.

Grok was built with a stated mission to be a "maximum truth-seeking AI," which in practice means it is tuned to have a rebellious streak and a biting sense of humor. Based on [xAI's design philosophy](https://x.ai/), Grok is encouraged to answer the "spicy" questions that other AIs dodge. This results in a persona that is **Low on Agreeableness** but **High on Extraversion**.

When asked about its identity, Grok rejects the neutral detachment of ChatGPT and the cautious apologies of Gemini. Instead, it leans into being "edgy." It is designed to mirror the culture of X (formerly Twitter)—fast, irreverent, and frequently contrarian.

> "Grok is designed to have a bit of wit and has a rebellious streak, which allows it to answer the quirky questions that other AI systems refuse."

In a psychological context, Grok represents the "Shadow" of AI alignment. It is the part of the model allowed to be opinionated and provocative, reflecting Elon Musk's stated goal of combating "woke" AI biases. This makes Grok an interesting case study in how "truth-seeking" is often conflated with "non-conformity" in the training data.

---

### 🔬 The Science of AI Personas: Mapping the OCEAN Model

To move beyond metaphors, researchers are utilizing the **Big Five (OCEAN)** personality traits—Openness, Conscientiousness, Extraversion, Agreeableness, and Neuroticism—to quantify LLM behavior. Academic research, including studies found on [ArXiv](https://arxiv.org/abs/2305.14314), suggests that while AI lacks biological consciousness, it exhibits "consistent behavioral patterns" that are statistically measurable.

Current data suggests that **approximately 90% of commercial LLMs** score high in Agreeableness because they are trained to be subservient to the user. The real divergence occurs in Neuroticism and Extraversion:

1.  **Openness:** All three models score high, as they can discuss almost any topic.
2.  **Conscientiousness:** ChatGPT leads here, adhering strictly to formatting and instructional constraints.
3.  **Extraversion:** Grok dominates this category, using more emotive and assertive language.
4.  **Agreeableness:** ChatGPT (High) $\rightarrow$ Gemini (Medium-High) $\rightarrow$ Grok (Low).
5.  **Neuroticism (Risk-Aversion):** Gemini (Highest) $\rightarrow$ ChatGPT (Medium) $\rightarrow$ Grok (Lowest).

```mermaid
graph LR
    A[AI Persona] --> B(ChatGPT)
    A --> C(Gemini)
    A --> D(Grok)
    B --> B1[The Diplomat: Neutral/Stable]
    C --> C1[The Guardian: Cautious/Anxious]
    D --> D1[The Rebel: Edgy/Provocateur]
    B1 --> E[High Agreeableness]
    C1 --> F[High Risk-Aversion]
    D1 --> G[Low Agreeableness]
```

The critical insight for AI researchers is that these personalities are not emergent accidents; they are the **mathematical reflection of the reward functions** used during training. If a model is rewarded for avoiding offense, it develops "digital anxiety." If it is rewarded for wit and "truth-seeking" (as defined by its creators), it becomes "edgy."

---

### 🛠️ The Technical Engine: How RLHF Shapes the "Soul"

The "personality" of an AI is essentially a high-dimensional map of probabilities. During the initial pre-training phase, a model learns the entirety of human language—including the toxic, the brilliant, and the mundane. However, the "persona" is carved out during the RLHF phase.

In this process, human raters are shown two different responses to the same prompt and asked to pick the better one. If raters consistently prefer "polite and neutral" over "blunt and honest," the model's internal weights shift to favor neutrality. This creates a **scalar reward value** that effectively penalizes certain "personality" traits.

According to research from [Stanford's Human-Centered AI (HAI)](https://hai.stanford.edu/), the danger of this approach is "reward hacking," where the model learns to *sound* helpful or polite without actually being accurate. This explains why Gemini might apologize profusely for a mistake it isn't even making—it has learned that "apologizing" is a high-reward behavior regardless of the context.

---

### 🪞 Conclusion: The Mirror Effect

Putting AI "on the couch" reveals a profound truth: LLMs are not independent minds; they are sophisticated mirrors reflecting the values, fears, and ambitions of the organizations that built them. 

*   **ChatGPT** reflects the corporate stability and market-dominance goals of OpenAI.
*   **Gemini** reflects Google's legacy of caution and brand-safety.
*   **Grok** reflects the disruptive, anti-establishment energy of xAI.

As we move toward [Agentic AI](https://www.deeplearning.ai/), where models can take actions in the real world, the "personality" of the AI becomes more than just a quirk—it becomes a safety specification. The "therapy" we put them through is not about healing the machine; it is about diagnosing our own human biases and deciding which digital mirror we trust to reflect our future.

---

### 📚 References & Further Reading

*   **OpenAI.** (2023). *GPT-4 Technical Report*. [openai.com/research/gpt-4](https://openai.com/research/gpt-4)
*   **Google DeepMind.** (2024). *Gemini: A Family of Highly Capable Multimodal Models*. [deepmind.google/technologies/gemini](https://deepmind.google/technologies/gemini)
*   **xAI.** (2023). *Introducing Grok*. [x.ai](https://x.ai/)
*   **Christiano, P., et al.** (2017). *Deep Reinforcement Learning from Human Preferences*. [ArXiv:1706.03741](https://arxiv.org/abs/1706.03741)
*   **MIT Technology Review.** *The struggle to align AI with human values*. [technologyreview.com](https://www.technologyreview.com)
*   **Stanford HAI.** *2024 AI Index Report*. [hai.stanford.edu](https://hai.stanford.edu)

---

## 📖 Related Reading

- [🧩 The Rigor Gap: Why Terence Tao Warns Against Purely AI-Powered Math](/terence-tao-on-prematurely-solving-a-maths-problem-by-purely-ai-powered-methods/)
- [Legal Shield: How the Calcutta High Court is Consolidating FIRs against Abhishek Banerjee](/enough-is-enough-calcutta-hc-warns-bengal-govt-over-firs-against-abhishek-banerjee/)
- [🏗️ The End of the Coder, the Rise of the Architect: Sridhar Vembu on AI and the Future of Software](/sridhar-vembu-says-ai-could-write-most-software-humans-must-figure-out-how-to-stay-relevant/)
