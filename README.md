# ❌⭕ Tic-Tac-Toe via Pull Requests

Welcome to the **PR-Powered Tic-Tac-Toe Game**! Play against an unbeatable Minimax AI bot directly using GitHub Pull Requests.

---

### 🎮 Current Board

| Column 0 | Column 1 | Column 2 |
|:---:|:---:|:---:|
| `[0]` | `[1]` | `[2]` |
| `[3]` | `[4]` | `[5]` |
| `[6]` | `[7]` | `[8]` |

> **Status:** New match ready!

---

### 🕹️ How to Play

1. **Fork** this repository.
2. Edit [`game_state.json`](game_state.json) in your browser.
3. Replace one empty `null` in the `"tiles"` array with `"X"`:
   ```json
   "tiles": [
     "X",   <-- your move on tile 0
     null,
     null,
     ...
   ]
   ```
4. **Submit a Pull Request** targeting `master`.
5. GitHub Actions will:
   - Validate your move in seconds.
   - Calculate the AI Bot's countermove (`⭕`).
   - Merge your PR and update the live board!

---

### 🏆 Scoreboard

| Metric | Score |
|---|---|
| 🧑‍💻 Community Wins | **0** |
| 🤖 AI Bot Wins | **0** |
| 🤝 Draws | **0** |

### 📜 Recent Matches

| Player | Result |
|---|---|
| *No games played yet* | - |

