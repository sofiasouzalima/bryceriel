"""
BRYCERIEL ARCHIVE — Script de Coleta
=====================================
Coleta posts + comentários do r/Bryceriel via Arctic Shift
e usa a API do Claude para categorizar, classificar por nível
e identificar parallels/receipts automaticamente.

COMO USAR:
1. Instala dependências: pip install requests anthropic
2. Coloca sua chave da API Anthropic na variável ANTHROPIC_KEY
3. Roda: python coletar.py
4. O arquivo data/posts.json será gerado/atualizado

PRIMEIRA VEZ: coleta tudo (~pode demorar dependendo do volume)
PRÓXIMAS VEZES: só coleta posts novos
"""

import requests
import json
import os
import time
from datetime import datetime

# ─── CONFIGURAÇÃO ────────────────────────────────────────────
SUBREDDIT = "Bryceriel"
DATA_FILE = "data/posts.json"
ANTHROPIC_KEY = "SUA_CHAVE_AQUI"  # <- coloca sua chave da API Anthropic
MAX_COMMENTS_PER_POST = 20         # top comentários por upvote
MIN_COMMENT_UPVOTES = 3            # ignora comentários com menos disso
AI_CONFIDENCE_THRESHOLD = 0.70     # abaixo disso vai para revisão manual
SKIP_TAGS = ["toxic thursday", "toxicthursday"]  # tags para ignorar
BASE_URL = "https://arctic-shift.photon-reddit.com/api"

# Tags que indicam possível portfolio/fanart
PORTFOLIO_TAGS = [
    "bryceriel content", "bryceriel or die",
    "bryceriel week", "joined the dark side",
    "fan art", "celebration"
]

# ─── CARREGAR DADOS EXISTENTES ────────────────────────────────
os.makedirs("data", exist_ok=True)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        existing = json.load(f)
    existing_ids = {p["id"] for p in existing}
    print(f"Arquivo existente: {len(existing)} posts já salvos.")
else:
    existing = []
    existing_ids = set()
    print("Nenhum arquivo encontrado. Coletando tudo do zero...")

# ─── COLETAR POSTS ────────────────────────────────────────────
print(f"\nColetando posts de r/{SUBREDDIT}...")
new_posts_raw = []
after = None
stopped = False

while not stopped:
    url = f"{BASE_URL}/posts?subreddit={SUBREDDIT}&limit=100&sort=new"
    if after:
        url += f"&after={after}"

    try:
        resp = requests.get(url, timeout=30)
        data = resp.json().get("data", [])
    except Exception as e:
        print(f"  Erro ao coletar posts: {e}")
        break

    if not data:
        break

    for post in data:
        if post["id"] in existing_ids:
            print(f"  Post já existente encontrado. Parando coleta.")
            stopped = True
            break

        # Pula tags bloqueadas
        flair = (post.get("link_flair_text") or "").lower()
        if any(skip in flair for skip in SKIP_TAGS):
            print(f"  Pulando post com tag bloqueada: {flair}")
            continue

        new_posts_raw.append(post)

    if data:
        after = data[-1]["id"]
    print(f"  {len(new_posts_raw)} posts novos encontrados...")
    time.sleep(0.5)

print(f"\nTotal de posts novos para processar: {len(new_posts_raw)}")

# ─── COLETAR COMENTÁRIOS ─────────────────────────────────────
def get_comments(post_id, post_author):
    """Coleta top comentários de um post."""
    try:
        url = f"{BASE_URL}/comments?link_id={post_id}&limit=100&sort=top"
        resp = requests.get(url, timeout=30)
        comments_raw = resp.json().get("data", [])

        comments = []
        for c in comments_raw:
            if c.get("score", 0) < MIN_COMMENT_UPVOTES:
                continue
            if c.get("author") == "[deleted]":
                continue

            comments.append({
                "author": c.get("author", ""),
                "body": c.get("body", "")[:1000],  # limita tamanho
                "upvotes": c.get("score", 0),
                "is_op": c.get("author") == post_author,
                "ai_adds_evidence": False  # será preenchido pela IA
            })

        # Ordena: OP primeiro, depois por upvotes
        comments.sort(key=lambda x: (-int(x["is_op"]), -x["upvotes"]))
        return comments[:MAX_COMMENTS_PER_POST]

    except Exception as e:
        print(f"    Erro ao coletar comentários: {e}")
        return []

# ─── CATEGORIZAÇÃO COM IA ─────────────────────────────────────
def categorize_with_ai(post, comments):
    """Usa Claude para categorizar um post e seus comentários."""

    if not ANTHROPIC_KEY or ANTHROPIC_KEY == "SUA_CHAVE_AQUI":
        # Sem chave da API: categorização básica pelas tags do Reddit
        return basic_categorize(post, comments)

    comments_text = "\n".join([
        f"[{c['author']} | {c['upvotes']} upvotes{'| OP' if c['is_op'] else ''}]: {c['body']}"
        for c in comments[:10]
    ])

    reddit_tags = post.get("link_flair_text") or ""
    has_image = bool(post.get("url", "").endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")))

    prompt = f"""You are an AI assistant for a Bryceriel fan archive (r/Bryceriel). 
Bryceriel is a fan ship pairing Bryce Quinlan (Crescent City) and Azriel (ACOTAR) from Sarah J. Maas's Maasverse.

Analyze this Reddit post and its top comments, then return ONLY valid JSON with no other text.

POST TITLE: {post.get('title', '')}
POST BODY: {post.get('selftext', '')[:2000]}
REDDIT TAG: {reddit_tags}
HAS IMAGE: {has_image}

TOP COMMENTS:
{comments_text}

Return this exact JSON structure:
{{
  "ai_category": "theory|parallels|receipts|maasverse|meme|fanfic|news|discussion|question|rant|announcement",
  "ai_level": "brycurious|student|scholar",
  "ai_tags": ["tag1", "tag2", "tag3"],
  "ai_is_parallel": true|false,
  "ai_is_receipt": true|false,
  "ai_portfolio_candidate": true|false,
  "ai_confidence": 0.0-1.0,
  "ai_summary": "2-3 sentence summary of the theory/post",
  "ai_key_points": ["point1", "point2", "point3"],
  "ai_related_themes": ["dusk-court|weapons|SJM-pattern|mating-bond|starborn|hunt-critical|crossover|prophecy|timeline"],
  "ai_adds_evidence_comments": [0, 1, 2],
  "needs_review": true|false
}}

CATEGORIZATION RULES:
- brycurious: intro content, explains basics, no prior knowledge assumed
- student: assumes basic knowledge, presents evidence, compares scenes, SJM patterns
- scholar: deep lore, time travel theories, complex multi-book analysis, obscure connections

- parallels: compares a Bryceriel moment to a canon SJM couple moment from other books
- receipts: direct textual evidence from the books (quotes, descriptions)
- ai_portfolio_candidate: true ONLY if has image AND reddit tag suggests fanart/community content
- needs_review: true if confidence < 0.70 OR category is ambiguous
- ai_adds_evidence_comments: indices (0-based) of comments that add meaningful new evidence

Be strict. "brycurious" is only for genuinely introductory content."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )

        text = resp.json()["content"][0]["text"].strip()
        # Remove markdown code blocks if present
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)

        # Mark which comments add evidence
        for i, c in enumerate(comments):
            c["ai_adds_evidence"] = i in result.get("ai_adds_evidence_comments", [])

        return result

    except Exception as e:
        print(f"    Erro na IA: {e}. Usando categorização básica.")
        return basic_categorize(post, comments)


def basic_categorize(post, comments):
    """Categorização básica sem IA — usa tags do Reddit."""
    flair = (post.get("link_flair_text") or "").lower()
    title = post.get("title", "").lower()
    body = post.get("selftext", "").lower()
    has_image = bool(post.get("url", "").endswith((".jpg",".jpeg",".png",".gif",".webp")))

    # Categoria
    if "theory" in flair or "parallel" in flair or "receipt" in flair:
        cat = "theory"
    elif "meme" in flair:
        cat = "meme"
    elif "fan fic" in flair or "fanfic" in flair:
        cat = "fanfic"
    elif "news" in flair:
        cat = "news"
    elif "discussion" in flair:
        cat = "discussion"
    elif "question" in flair:
        cat = "question"
    elif "rant" in flair or "vent" in flair:
        cat = "rant"
    elif any(t in flair for t in PORTFOLIO_TAGS):
        cat = "bryceriel-content"
    else:
        cat = "discussion"

    # Nível básico por comprimento e complexidade
    body_len = len(post.get("selftext", ""))
    if body_len < 300:
        level = "brycurious"
    elif body_len < 1500:
        level = "student"
    else:
        level = "scholar"

    # Portfolio candidate
    portfolio = has_image and any(t in flair for t in [p.lower() for p in PORTFOLIO_TAGS])

    return {
        "ai_category": cat,
        "ai_level": level,
        "ai_tags": [flair] if flair else [],
        "ai_is_parallel": "parallel" in flair,
        "ai_is_receipt": "receipt" in flair,
        "ai_portfolio_candidate": portfolio,
        "ai_confidence": 0.60,
        "ai_summary": post.get("title", ""),
        "ai_key_points": [],
        "ai_related_themes": [],
        "needs_review": True  # sem IA, sempre pede revisão
    }


# ─── PROCESSAR POSTS NOVOS ────────────────────────────────────
processed = []

for i, post in enumerate(new_posts_raw):
    print(f"\nProcessando {i+1}/{len(new_posts_raw)}: {post.get('title','')[:60]}...")

    # Coleta comentários
    print(f"  Coletando comentários...")
    comments = get_comments(post["id"], post.get("author", ""))
    print(f"  {len(comments)} comentários relevantes encontrados.")

    # Categoriza com IA
    print(f"  Categorizando com IA...")
    ai_data = categorize_with_ai(post, comments)

    # Detecta se tem imagem
    url = post.get("url", "")
    has_image = url.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
    image_url = url if has_image else None

    # Monta o objeto final
    processed_post = {
        # Dados originais do Reddit
        "id": post["id"],
        "title": post.get("title", ""),
        "body": post.get("selftext", ""),
        "author": post.get("author", ""),
        "upvotes": post.get("score", 0),
        "comments_count": post.get("num_comments", 0),
        "date": datetime.fromtimestamp(post.get("created_utc", 0)).strftime("%Y-%m-%d"),
        "year": datetime.fromtimestamp(post.get("created_utc", 0)).strftime("%Y"),
        "month": datetime.fromtimestamp(post.get("created_utc", 0)).strftime("%Y-%m"),
        "reddit_url": f"https://reddit.com{post.get('permalink', '')}",
        "reddit_tag": post.get("link_flair_text", ""),
        "has_image": has_image,
        "image_url": image_url,

        # Dados dos comentários
        "top_comments": comments,

        # Dados da IA
        "ai_category": ai_data.get("ai_category", "discussion"),
        "ai_level": ai_data.get("ai_level", "student"),
        "ai_tags": ai_data.get("ai_tags", []),
        "ai_is_parallel": ai_data.get("ai_is_parallel", False),
        "ai_is_receipt": ai_data.get("ai_is_receipt", False),
        "ai_portfolio_candidate": ai_data.get("ai_portfolio_candidate", False),
        "ai_confidence": ai_data.get("ai_confidence", 0.6),
        "ai_summary": ai_data.get("ai_summary", ""),
        "ai_key_points": ai_data.get("ai_key_points", []),
        "ai_related_themes": ai_data.get("ai_related_themes", []),
        "needs_review": ai_data.get("needs_review", True),

        # Status no site (editável pelo admin)
        "approved": not ai_data.get("needs_review", True),
        "portfolio_approved": False,  # portfolio sempre precisa aprovação manual
        "manually_edited": False,
        "hidden": False,

        # Sugestões de posts relacionados (preenchido depois)
        "related_post_ids": [],

        # Canon updates (preenchido após releases de novos livros)
        "canon_updates": []
    }

    processed.append(processed_post)
    time.sleep(0.3)  # evita rate limiting

# ─── CALCULAR POSTS RELACIONADOS ─────────────────────────────
print("\nCalculando posts relacionados...")

all_posts = processed + existing

def similarity_score(post_a, post_b):
    """Score simples de similaridade por tags e temas."""
    if post_a["id"] == post_b["id"]:
        return 0

    score = 0
    themes_a = set(post_a.get("ai_related_themes", []))
    themes_b = set(post_b.get("ai_related_themes", []))
    tags_a = set(post_a.get("ai_tags", []))
    tags_b = set(post_b.get("ai_tags", []))

    score += len(themes_a & themes_b) * 3
    score += len(tags_a & tags_b) * 2

    if post_a.get("ai_is_parallel") and post_b.get("ai_is_parallel"):
        score += 2
    if post_a.get("ai_is_receipt") and post_b.get("ai_is_receipt"):
        score += 2
    if post_a.get("ai_level") == post_b.get("ai_level"):
        score += 1

    return score

for post in processed:
    scores = [(other["id"], similarity_score(post, other)) for other in all_posts]
    scores.sort(key=lambda x: -x[1])
    post["related_post_ids"] = [s[0] for s in scores[:5] if s[1] > 0]

# ─── SALVAR ──────────────────────────────────────────────────
all_posts_final = processed + existing

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(all_posts_final, f, ensure_ascii=False, indent=2)

# Relatório
needs_review = sum(1 for p in processed if p["needs_review"])
portfolio_pending = sum(1 for p in processed if p["ai_portfolio_candidate"])
parallels = sum(1 for p in processed if p["ai_is_parallel"])
receipts = sum(1 for p in processed if p["ai_is_receipt"])

print(f"""
═══════════════════════════════════════
COLETA CONCLUÍDA
═══════════════════════════════════════
Posts novos coletados:    {len(processed)}
Total no arquivo:         {len(all_posts_final)}

Posts para revisar:       {needs_review}
Portfolio pendente:       {portfolio_pending}
Parallels identificados:  {parallels}
Receipts identificados:   {receipts}

Arquivo salvo em: {DATA_FILE}
═══════════════════════════════════════
Próximo passo: abrir index.html e fazer
login no painel admin para revisar.
""")
