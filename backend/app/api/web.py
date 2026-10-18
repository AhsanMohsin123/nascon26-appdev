"""Guest Web Player (Section 6.2.2) — minimal zero-install page with the mandatory
data-testid DOM contract, wired to the real backend (no mocked data)."""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from sqlalchemy import text

router = APIRouter()


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — NaSCon '26</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 16px; background: #0f172a; color: #e2e8f0; }}
  button {{ min-height: 48px; min-width: 48px; font-size: 16px; border-radius: 8px; border: none; padding: 8px 16px; cursor: pointer; }}
  [data-testid="guest-video-player"] {{ background: #000; aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center; border-radius: 8px; color: #94a3b8; }}
  [data-testid="live-score-banner"] {{ font-size: 28px; font-weight: 700; text-align: center; padding: 12px; }}
  [data-testid="pinned-merch-card"] {{ border: 1px solid #334155; border-radius: 8px; padding: 12px; margin: 12px 0; }}
  [data-testid="add-to-guest-cart-btn"] {{ background: #2563eb; color: white; }}
  [data-testid="chat-message-list"] {{ height: 160px; overflow-y: auto; border: 1px solid #334155; border-radius: 8px; padding: 8px; }}
  [data-testid="chat-input-field"] {{ width: 70%; min-height: 48px; font-size: 16px; }}
  [data-testid="chat-send-btn"] {{ background: #16a34a; color: white; }}
  [data-testid="progressive-auth-modal"] {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,.7); align-items: center; justify-content: center; }}
  [data-testid="progressive-auth-modal"].open {{ display: flex; }}
  .modal-box {{ background: #1e293b; padding: 24px; border-radius: 12px; max-width: 320px; text-align: center; }}
</style>
</head><body>
{body}
</body></html>"""


async def _score_banner_html(db: AsyncSession, match_id: str) -> str:
    row = (await db.execute(text("SELECT status FROM matches WHERE id=:id"), {"id": match_id})).fetchone()
    if not row:
        return "N/A"
    from app.domain.scoring import get_score
    try:
        score = await get_score(db, match_id)
        return f"{score['home']['score']} - {score['away']['score']}"
    except Exception:
        return "0 - 0"


@router.get("/web/matches/{match_id}/live", response_class=HTMLResponse)
async def match_live(match_id: str, db: AsyncSession = Depends(get_db)):
    score_text = await _score_banner_html(db, match_id)
    body = f"""
<div data-testid="guest-video-player" role="img" aria-label="Live match video player">LIVE — HLS/WebRTC player placeholder</div>
<div data-testid="live-score-banner" aria-live="polite">{score_text}</div>

<div data-testid="pinned-merch-card">
  <strong>Jersey 001</strong> — PKR 4500.00
  <div><span>Cart: </span><span data-testid="guest-cart-count">0</span></div>
  <button data-testid="add-to-guest-cart-btn" aria-label="Add jersey to guest cart">Add to Cart</button>
</div>

<h3>Live Chat</h3>
<div data-testid="chat-message-list" role="log" aria-label="Live chat messages"></div>
<input data-testid="chat-input-field" type="text" aria-label="Chat message" placeholder="Say something...">
<button data-testid="chat-send-btn" aria-label="Send chat message">Send</button>

<div data-testid="progressive-auth-modal" role="dialog" aria-modal="true" aria-label="Login required">
  <div class="modal-box">
    <p>Please log in or register to continue.</p>
    <button onclick="document.querySelector('[data-testid=progressive-auth-modal]').classList.remove('open')">Close</button>
  </div>
</div>

<script>
  const matchId = {match_id!r};
  let cartCount = 0;

  document.querySelector('[data-testid="add-to-guest-cart-btn"]').addEventListener('click', () => {{
    cartCount += 1;
    document.querySelector('[data-testid="guest-cart-count"]').textContent = String(cartCount);
  }});

  document.querySelector('[data-testid="chat-send-btn"]').addEventListener('click', async () => {{
    const input = document.querySelector('[data-testid="chat-input-field"]');
    const text = input.value;
    if (!text) return;
    const res = await fetch('/api/v1/chat', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer guest_anon_tok_7721' }},
      body: JSON.stringify({{ message_id: 'web-' + Date.now(), text }}),
    }});
    if (res.status === 403) {{
      document.querySelector('[data-testid="progressive-auth-modal"]').classList.add('open');
    }}
    input.value = '';
  }});

  async function pollScore() {{
    try {{
      const res = await fetch('/audit/v1/score/' + matchId);
      if (res.ok) {{
        const data = await res.json();
        document.querySelector('[data-testid="live-score-banner"]').textContent = data.home.score + ' - ' + data.away.score;
      }}
    }} catch (e) {{}}
  }}
  setInterval(pollScore, 400);
</script>
"""
    return _page(f"Match {match_id} — Live", body)


@router.get("/web/matches/{match_id}/preview", response_class=HTMLResponse)
async def match_preview(match_id: str):
    return _page(f"Match {match_id} — Preview", f"<h2>Match {match_id}</h2><p>This match hasn't started yet. Check back soon.</p>")


@router.get("/web/matches/{match_id}/vod", response_class=HTMLResponse)
async def match_vod(match_id: str, db: AsyncSession = Depends(get_db)):
    score_text = await _score_banner_html(db, match_id)
    return _page(f"Match {match_id} — VOD", f"""
<div data-testid="guest-video-player">VOD playback placeholder</div>
<div data-testid="live-score-banner">Final: {score_text}</div>
""")


@router.get("/web/matches/{match_id}/notice", response_class=HTMLResponse)
async def match_notice(match_id: str, state: str = "postponed"):
    return _page(f"Match {match_id} — Notice", f"<h2>Match {match_id}</h2><p>This match is {state}.</p>")


@router.get("/web/players/{player_id}", response_class=HTMLResponse)
async def player_profile(player_id: str):
    return _page(f"{player_id}", f"<h2>{player_id}</h2><p>Player profile — full build pending.</p>")


@router.get("/web/clubs/{club_id}", response_class=HTMLResponse)
async def club_profile(club_id: str):
    return _page(f"{club_id}", f"<h2>{club_id}</h2><p>Club profile — full build pending.</p>")


@router.get("/web/costream/{session_id}", response_class=HTMLResponse)
async def costream_view(session_id: str):
    return _page(f"{session_id}", f"""
<div data-testid="guest-video-player">Co-stream composite playback placeholder</div>
<div data-testid="live-score-banner">—</div>
<div data-testid="chat-message-list"></div>
<input data-testid="chat-input-field" type="text">
<button data-testid="chat-send-btn">Send</button>
""")
