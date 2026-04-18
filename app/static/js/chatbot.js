/* Floating chat button + panel – clean v4 */
(function () {
  // ────────── insert markup ──────────
  const html = `
  <div id="bot-box" class="bot-hidden">
    <div class="bot-header">
      Eventory Bot
      <span id="bot-close">×</span>
    </div>
    <div id="bot-log" class="bot-log"></div>
    <form id="bot-form" class="bot-form">
      <input id="bot-input" class="bot-input" placeholder="Type a message…" autocomplete="off">
    </form>
  </div>
  <button id="bot-toggle" class="bot-toggle">💬</button>`;
  document.body.insertAdjacentHTML("beforeend", html);

  // ────────── helpers ──────────
  const box   = document.getElementById("bot-box");
  const log   = document.getElementById("bot-log");
  const input = document.getElementById("bot-input");

  /**
   * Very minimal Markdown renderer:
   *  - [Label](url) → <a href="url">Label</a>
   *  - preserves other text and line breaks
   */
  function renderMarkdown(text) {
    return text
      .split("\n")
      .map(line =>
        line.replace(
          /\[([^\]]+)]\(([^)]+)\)/g,
          (_, label, url) =>
            `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`
        )
      )
      .join("<br>");
  }

  /**
   * Append a message bubble, then save to sessionStorage.
   */
  function addLine(text, me) {
    const div = document.createElement("div");
    div.className = "bot-msg " + (me ? "bot-me" : "bot-bot");
    div.innerHTML = renderMarkdown(text);
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;

    // persist history in this tab
    const hist = JSON.parse(sessionStorage.getItem("botHist") || "[]");
    hist.push({ me, text });
    sessionStorage.setItem("botHist", JSON.stringify(hist));
  }

  // ────────── UI wiring ──────────
  document.getElementById("bot-toggle").onclick = () => {
    const hidden = box.classList.toggle("bot-hidden");
    if (!hidden) input.focus();
  };
  document.getElementById("bot-close").onclick = () => {
    box.classList.add("bot-hidden");
    sessionStorage.removeItem("botHist"); // clear on close
  };

  // restore history
  JSON.parse(sessionStorage.getItem("botHist") || "[]").forEach(({ me, text }) =>
    addLine(text, me)
  );

  // handle send
  document.getElementById("bot-form").addEventListener("submit", e => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    addLine(text, true);
    input.value = "";

    fetch("/chatbot/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    })
      .then(r => r.json())
      .then(j => addLine(j.reply, false))
      .catch(() => addLine("⚠️ Error talking to server.", false));
  });

  // ────────── minimal CSS ──────────
  const css = `
  #bot-box           {position:fixed;bottom:90px;right:20px;width:330px;height:440px;
                      background:#fff;border:1px solid #ccc;border-radius:8px;
                      display:flex;flex-direction:column;z-index:9999;
                      font-family:system-ui,sans-serif;font-size:14px;}
  #bot-box.bot-hidden{display:none;}
  .bot-header        {background:#343a40;color:#fff;padding:8px 12px;font-weight:600;
                      border-radius:8px 8px 0 0;user-select:none}
  #bot-close         {float:right;cursor:pointer;font-size:18px;margin-left:6px}
  .bot-log           {flex:1;padding:10px;overflow-y:auto;background:#fafafa}
  .bot-form          {display:flex;border-top:1px solid #ddd}
  .bot-input         {flex:1;border:none;padding:10px;font-size:14px}
  .bot-input:focus   {outline:none}
  .bot-toggle        {position:fixed;bottom:20px;right:20px;
                      background:#ffc107;border:none;border-radius:50%;
                      width:56px;height:56px;font-size:26px;
                      box-shadow:0 2px 6px rgba(0,0,0,.3);cursor:pointer}
  .bot-msg           {margin:6px 0;max-width:90%;padding:8px 10px;border-radius:12px;
                      line-height:1.35}
  .bot-me            {background:#007bff;color:#fff;margin-left:auto;
                      border-bottom-right-radius:0}
  .bot-bot           {background:#e9ecef;color:#111;margin-right:auto;
                      border-bottom-left-radius:0}
  .bot-msg a         {color:inherit;text-decoration:underline}`;
  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);
})();
