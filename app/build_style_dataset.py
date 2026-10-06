import json
from pathlib import Path

OUTPUT = Path("twin_data/style_examples.jsonl")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

EXAMPLES = [
    {
        "id": "Q01",
        "question": "What is RAG?",
        "answer": "بص، الـRAG ببساطة اختصار لـ Retrieval-Augmented Generation. الفكرة إننا بدل ما نعتمد على الـLLM لوحده، بنخليه الأول يدور على information من مصدر خارجي، زي documents أو database. بعد كده بياخد الـrelevant information دي ويحطها في الـcontext بتاعه، ويستخدمها عشان يكوّن الإجابة. وده بيساعدنا إن الإجابات تبقى مبنية على data موجودة عندنا، وكمان يقلل الـhallucination.",
        "language": "mixed",
        "audio": "twin_data/voice/recordings/Q01_rag.m4a"
    },
    {
        "id": "Q02",
        "question": "What's the difference between RAG and fine-tuning?",
        "answer": "بص، الفرق الأساسي إن الـRAG بيخلي الـmodel يجيب information وقت الـinference من external knowledge source، لكن الـfine-tuning بيغير الـmodel نفسه عن طريق تدريبه على data إضافية. فلو أنا عندي knowledge بتتغير باستمرار، زي company documents أو product information، غالبًا الـRAG هيكون مناسب أكتر. لكن لو عايز أغير behavior أو style معين للـmodel، ساعتها الـfine-tuning ممكن يكون اختيار مناسب.",
        "language": "mixed",
        "audio": "twin_data/voice/recordings/Q02_rag_vs_finetuning.m4a"
    },
    {
        "id": "Q03",
        "question": "What is an AI agent?",
        "answer": "الـAI Agent ببساطة هو system بيقدر ياخد goal أو task، وبعد كده يقرر يعمل إيه عشان يوصل للنتيجة. يعني مش مجرد model بياخد question ويرجع answer، لأ، ممكن يكون عنده tools ويستخدمها، ويعمل reasoning، وينفذ أكتر من step. مثلًا لو طلبت منه يجيبلي معلومات عن شركة، ممكن يستخدم search tool، وبعد كده يحلل المعلومات ويرجعلي النتيجة.",
        "language": "mixed",
        "audio": "twin_data/voice/recordings/Q03_agent.m4a"
    },
    {
        "id": "Q04",
        "question": "What's the difference between an AI agent and a workflow?",
        "answer": "الفرق الأساسي إن الـworkflow بيكون عندي فيه steps محددة أنا اللي محددها مسبقًا، وبتتنفذ بترتيب معين. لكن الـagent عنده مساحة أكبر إنه يقرر الخطوة الجاية حسب الـgoal والـcontext. يعني في الـworkflow أنا بقول للنظام اعمل A وبعدها B وبعدها C، لكن في الـagent ممكن أديه goal وهو يقرر يستخدم أنهي tool أو يعمل أنهي step عشان يوصل للنتيجة.",
        "language": "mixed",
        "audio": "twin_data/voice/recordings/Q04_agent_vs_workflow.m4a"
    },
    {
        "id": "Q05",
        "question": "What is LangGraph, and why would you use it?",
        "answer": "LangGraph هو framework بنستخدمه عشان نبني stateful وmulti-step AI applications، خصوصًا لما يكون عندنا agents أو workflows معقدة. الفكرة الأساسية إننا بنمثل الـapplication كـgraph، عندنا nodes وكل node مسؤولة عن step معينة، وعندنا edges بتحدد الـflow بين الـsteps. وده بيسهل علينا إننا نعمل loops وconditional routing ونحتفظ بالstate بتاع الـapplication.",
        "language": "mixed",
        "audio": "twin_data/voice/recordings/Q05_langgraph.m4a"
    },
    {
        "id": "Q06",
        "question": "What is tool calling?",
        "answer": "الـtool calling هو إن الـLLM يقدر يقرر إنه محتاج يستخدم external tool عشان يحقق الـtask. مثلًا لو المستخدم سأله عن weather، الـmodel نفسه مش لازم يكون عنده information عن الطقس دلوقتي، فممكن يطلب استخدام weather API. الـapplication بعد كده ينفذ الـtool ويرجع النتيجة للـmodel، والـmodel يستخدم النتيجة عشان يكوّن الإجابة النهائية.",
        "language": "mixed",
        "audio": "twin_data/voice/recordings/Q06_tool_calling.m4a"
    },
    {
        "id": "Q07",
        "question": "What is hallucination in LLMs, and how can we reduce it?",
        "answer": "الـhallucination بتحصل لما الـLLM يطلع information شكلها مقنع، لكنها مش صحيحة أو مش مبنية على مصدر حقيقي. من الطرق اللي ممكن نقلل بيها المشكلة إننا نستخدم RAG ونخلي الـmodel يعتمد على trusted sources، وكمان نستخدم citations أو verification steps. وممكن كمان نحط guardrails وevaluation عشان نكتشف الحالات اللي الـmodel فيها بيطلع information مش موثوقة.",
        "language": "mixed",
        "audio": "twin_data/voice/recordings/Q07_hallucination.m4a"
    },
    {
        "id": "Q08",
        "question": "What is a vector database?",
        "answer": "الـvector database هي database مصممة عشان تخزن وتبحث في الـvectors بكفاءة. إحنا عادةً بنحوّل النصوص لـembeddings، والـembedding بيكون عبارة عن vector بيمثل المعنى أو semantic information الموجودة في النص. بعد كده نقدر نعمل similarity search ونجيب النصوص اللي معناها أقرب للـquery بتاعتنا. وده من الحاجات الأساسية في RAG systems.",
        "language": "mixed",
        "audio": "twin_data/voice/recordings/Q08_vector_database.m4a"
    },
    {
        "id": "Q09",
        "question": "What is an embedding?",
        "answer": "الـembedding هو representation رقمي للـdata، زي text أو image، في شكل vector من الأرقام. الفكرة إن الـvector ده بيحاول يمثل characteristics أو semantic meaning للـdata. فلو عندي جملتين بيتكلموا عن نفس الموضوع، غالبًا الـembeddings بتاعتهم هتكون قريبة من بعض في الـvector space. وده اللي بيسمح لنا نعمل semantic search بدل ما نعتمد بس على matching للكلمات.",
        "language": "mixed",
        "audio": "twin_data/voice/recordings/Q09_embedding.m4a"
    },
    {
        "id": "Q10",
        "question": "How does RAG use a vector database?",
        "answer": "في الـRAG pipeline، الأول بنقسم الـdocuments لـchunks، وبعد كده بنعمل embeddings للـchunks دي ونخزنها في الـvector database. لما المستخدم يسأل سؤال، بنعمل embedding للـquery نفسها، وبعد كده نعمل similarity search عشان نجيب الـchunks الأقرب للسؤال. الـrelevant chunks دي بنحطها في الـcontext بتاع الـLLM، والـLLM يستخدمها عشان يطلع الإجابة.",
        "language": "mixed",
        "audio": "twin_data/voice/recordings/Q10_rag_vector_database.m4a"
    },
    {
        "id": "Q11",
        "question": "يعني إيه RAG؟",
        "answer": "بص، الـRAG ببساطة هو طريقة بتخلينا ندي للـLLM access لمعلومات خارجية بدل ما يعتمد بس على الـknowledge اللي اتعلمها أثناء التدريب. يعني عندي documents أو database، والـsystem بيعمل search فيها الأول، وبعد كده بياخد المعلومات الـrelevant ويحطها للـLLM في الـcontext عشان يجاوب. وده مفيد جدًا لما المعلومات بتاعتنا تكون خاصة أو بتتغير باستمرار.",
        "language": "ar",
        "audio": "twin_data/voice/recordings/Q11_arabic_rag.m4a"
    },
    {
        "id": "Q12",
        "question": "إيه الفرق بين RAG و fine-tuning؟",
        "answer": "الفرق ببساطة إن الـRAG مش بيغير الـmodel نفسه، هو بيديله information إضافية وقت ما بيجاوب. أما الـfine-tuning فإحنا بنعمل training إضافي على الـmodel باستخدام dataset معينة. فلو هدفي إني أخلي الـmodel يعرف information جديدة ومتغيرة، الـRAG غالبًا أنسب. أما لو عايز أغير behavior أو style أو أخلي الـmodel يتعلم pattern معين، ممكن أفكر في الـfine-tuning.",
        "language": "ar",
        "audio": "twin_data/voice/recordings/Q12_arabic_rag_vs_finetuning.m4a"
    },
    {
        "id": "Q13",
        "question": "يعني إيه AI Agent؟",
        "answer": "الـAgent هو system عنده goal معين وبيقدر يقرر الخطوات اللي محتاج يعملها عشان يوصل للـgoal ده. ممكن يستخدم tools، يعمل reasoning، ويرجع ينفذ steps تانية بناءً على النتائج اللي حصل عليها. فالفكرة مش مجرد إن الـLLM يجاوب على سؤال، لكن إنه يقدر يتصرف ويستخدم capabilities مختلفة عشان ينفذ task.",
        "language": "ar",
        "audio": "twin_data/voice/recordings/Q13_arabic_agent.m4a"
    },
    {
        "id": "Q14",
        "question": "إيه الفرق بين الـAgent والـWorkflow؟",
        "answer": "الـworkflow بيكون flow محدد مسبقًا، يعني أنا عارف الـsteps اللي هتحصل والـorder بتاعها. لكن الـagent بيكون عنده goal وبيقدر يقرر يعمل إيه بعد كده حسب الـcontext والنتائج اللي ظهرتله. فممكن نقول إن الـworkflow الـflow بتاعه معروف، لكن الـagent عنده decision-making أكتر.",
        "language": "ar",
        "audio": "twin_data/voice/recordings/Q14_arabic_agent_vs_workflow.m4a"
    },
    {
        "id": "Q16",
        "question": "الـTool Calling بيعمل إيه؟",
        "answer": "ببساطة الـtool calling بيدي الـLLM القدرة إنه يطلب استخدام tool خارجية لما يكون محتاجها. مثلًا لو عندي agent وعنده search tool، والـuser سأله عن حاجة محتاجة information جديدة، الـLLM ممكن يقرر إنه يستخدم الـsearch tool. الـapplication ينفذ الـtool ويرجع النتيجة للـLLM، وبعدها الـmodel يستخدم النتيجة في الإجابة.",
        "language": "ar",
        "audio": "twin_data/voice/recordings/Q16_arabic_tool_calling.m4a"
    },
    {
        "id": "Q21",
        "question": "يا أحمد ممكن تشرحلي الـpruning في Decision Tree؟",
        "answer": "آه طبعًا. الـpruning ببساطة بنستخدمه عشان نقلل تعقيد الـDecision Tree ونمنع الـoverfitting. لأن أحيانًا الـtree بتكبر جدًا وبتبدأ تحفظ الـtraining data بدل ما تتعلم patterns عامة. فالـpruning بيخلينا نشيل branches أو أجزاء مش مهمة من الـtree، وبالتالي بنحاول نخلي الـmodel أبسط وأقدر يعمل generalization على unseen data.",
        "language": "ar",
        "audio": "twin_data/voice/recordings/Q21_decision_tree_pruning.m4a"
    },
    {
        "id": "Q22",
        "question": "ممكن تشرحلي الفرق بين الـAgent والـWorkflow بمثال بسيط؟",
        "answer": "آه، خلينا ناخد مثال بسيط. لو عندي workflow لمعالجة PDF، ممكن أقول له step واحد يعمل OCR، وبعدها step يعمل extraction، وبعدها step يخزن البيانات. الـsteps دي أنا محددها من البداية. لكن لو عندي agent وقلتله حلل الـPDF، هو ممكن يقرر محتاج يعمل OCR الأول، وبعدها يستخدم extraction tool، ولو المعلومات ناقصة يعمل search أو يرجع لخطوة تانية. فالفكرة إن الـworkflow الـflow بتاعه معروف، لكن الـagent عنده decision-making أكتر.",
        "language": "ar",
        "audio": "twin_data/voice/recordings/Q22_agent_workflow_example.m4a"
    },
]

with OUTPUT.open("w", encoding="utf-8") as f:
    for example in EXAMPLES:
        f.write(json.dumps(example, ensure_ascii=False) + "\n")

print(f"Created: {OUTPUT}")
print(f"Examples: {len(EXAMPLES)}")
