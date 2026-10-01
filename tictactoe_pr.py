import argparse
import json
import os
import subprocess
import sys

WIN_COMBINATIONS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
    (0, 4, 8), (2, 4, 6)             # Diagonals
]

DEFAULT_STATE = {
    "status": "IN_PROGRESS",
    "turn": "X",
    "tiles": [None] * 9,
    "last_move": None,
    "last_player": None
}

DEFAULT_STATS = {
    "player_wins": 0,
    "bot_wins": 0,
    "draws": 0,
    "history": []
}


def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default.copy()
    return default.copy()


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_base_state(base_ref="origin/master", filepath="game_state.json"):
    try:
        cmd = ["git", "show", f"{base_ref}:{filepath}"]
        raw = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode("utf-8")
        return json.loads(raw)
    except Exception:
        return load_json(filepath, DEFAULT_STATE)


def check_winner(board, player):
    for a, b, c in WIN_COMBINATIONS:
        if board[a] == board[b] == board[c] == player:
            return True
    return False


def is_board_full(board):
    return all(cell is not None for cell in board)


def minimax(board, is_ai):
    if check_winner(board, "O"):
        return 10, None
    if check_winner(board, "X"):
        return -10, None
    if is_board_full(board):
        return 0, None

    if is_ai:
        best_score = -float("inf")
        best_move = None
        for i in range(9):
            if board[i] is None:
                board[i] = "O"
                score, _ = minimax(board, False)
                board[i] = None
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_score, best_move
    else:
        best_score = float("inf")
        best_move = None
        for i in range(9):
            if board[i] is None:
                board[i] = "X"
                score, _ = minimax(board, True)
                board[i] = None
                if score < best_score:
                    best_score = score
                    best_move = i
        return best_score, best_move


def validate_pr(base_state, head_state):
    b_tiles = base_state.get("tiles", [None] * 9)
    h_tiles = head_state.get("tiles", [None] * 9)

    if len(h_tiles) != 9:
        print("Error: Board must contain exactly 9 tiles.")
        sys.exit(1)

    diffs = []
    for i in range(9):
        if b_tiles[i] != h_tiles[i]:
            diffs.append((i, b_tiles[i], h_tiles[i]))

    if len(diffs) == 0:
        print("Error: No move detected! Change one empty null tile to 'X'.")
        sys.exit(1)

    if len(diffs) > 1:
        print(f"Error: Only 1 move allowed per PR! Detected {len(diffs)} changes.")
        sys.exit(1)

    idx, old_val, new_val = diffs[0]
    if old_val is not None:
        print(f"Error: Tile {idx} is already occupied by '{old_val}'.")
        sys.exit(1)

    if new_val != "X":
        print(f"Error: You must play as 'X'. Found '{new_val}'.")
        sys.exit(1)

    print(f"✅ Valid PR move: Player placed 'X' on Tile {idx}.")
    return idx


def execute_turn(player_move, player_name="Challenger"):
    state = load_json("game_state.json", DEFAULT_STATE)
    stats = load_json("stats.json", DEFAULT_STATS)

    board = state.get("tiles", [None] * 9)
    board[player_move] = "X"
    state["last_move"] = player_move
    state["last_player"] = player_name

    summary_msg = f"@{player_name} placed ❌ on tile {player_move}."

    # 1. Check if Human Won
    if check_winner(board, "X"):
        state["status"] = "HUMAN_WON"
        stats["player_wins"] += 1
        summary_msg += f" 🎉 **@{player_name} WON the game!**"
        record_history(stats, player_name, "Won")
        # Reset board for next game
        state["tiles"] = [None] * 9
        state["status"] = "NEW_GAME"
        save_json("game_state.json", state)
        save_json("stats.json", stats)
        render_readme(state, stats, summary_msg)
        return summary_msg

    # 2. Check if Draw
    if is_board_full(board):
        state["status"] = "DRAW"
        stats["draws"] += 1
        summary_msg += " 🤝 **Game ended in a DRAW!**"
        record_history(stats, player_name, "Draw")
        state["tiles"] = [None] * 9
        state["status"] = "NEW_GAME"
        save_json("game_state.json", state)
        save_json("stats.json", stats)
        render_readme(state, stats, summary_msg)
        return summary_msg

    # 3. AI Bot Turn (Minimax)
    _, ai_move = minimax(board, True)
    if ai_move is not None:
        board[ai_move] = "O"
        summary_msg += f" 🤖 AI Bot responded with ⭕ on tile {ai_move}."

        if check_winner(board, "O"):
            state["status"] = "BOT_WON"
            stats["bot_wins"] += 1
            summary_msg += " 💀 **AI Bot won the game!**"
            record_history(stats, player_name, "Lost")
            state["tiles"] = [None] * 9
            state["status"] = "NEW_GAME"
        elif is_board_full(board):
            state["status"] = "DRAW"
            stats["draws"] += 1
            summary_msg += " 🤝 **Game ended in a DRAW!**"
            record_history(stats, player_name, "Draw")
            state["tiles"] = [None] * 9
            state["status"] = "NEW_GAME"
        else:
            state["status"] = "IN_PROGRESS"

    save_json("game_state.json", state)
    save_json("stats.json", stats)
    render_readme(state, stats, summary_msg)
    return summary_msg


def record_history(stats, player, result):
    history_entry = {
        "player": player,
        "result": result
    }
    stats["history"].insert(0, history_entry)
    stats["history"] = stats["history"][:10]  # keep last 10 games


def render_readme(state, stats, latest_event="New match ready!"):
    board = state.get("tiles", [None] * 9)

    # Emoji display mapping
    def tile_str(idx):
        val = board[idx]
        if val == "X":
            return "❌"
        elif val == "O":
            return "⭕"
        else:
            return f"`[{idx}]`"

    board_md = f"""| Column 0 | Column 1 | Column 2 |
|:---:|:---:|:---:|
| {tile_str(0)} | {tile_str(1)} | {tile_str(2)} |
| {tile_str(3)} | {tile_str(4)} | {tile_str(5)} |
| {tile_str(6)} | {tile_str(7)} | {tile_str(8)} |"""

    history_rows = ""
    for h in stats.get("history", []):
        badge = "🏆 Won" if h["result"] == "Won" else ("🤝 Draw" if h["result"] == "Draw" else "❌ Lost")
        history_rows += f"| @{h['player']} | {badge} |\n"

    if not history_rows:
        history_rows = "| *No games played yet* | - |\n"

    readme_content = f"""# ❌⭕ Tic-Tac-Toe via Pull Requests

Welcome to the **PR-Powered Tic-Tac-Toe Game**! Play against an unbeatable Minimax AI bot directly using GitHub Pull Requests.

---

### 🎮 Current Board

{board_md}

> **Status:** {latest_event}

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
| 🧑‍💻 Community Wins | **{stats.get('player_wins', 0)}** |
| 🤖 AI Bot Wins | **{stats.get('bot_wins', 0)}** |
| 🤝 Draws | **{stats.get('draws', 0)}** |

### 📜 Recent Matches

| Player | Result |
|---|---|
{history_rows}
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("README.md successfully updated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PR Tic-Tac-Toe Game Engine")
    parser.add_argument("--mode", choices=["validate", "play", "render"], required=True)
    parser.add_argument("--base", default="origin/master")
    parser.add_argument("--player", default="Challenger")
    args = parser.parse_args()

    if args.mode == "validate":
        base_state = get_base_state(args.base)
        head_state = load_json("game_state.json", DEFAULT_STATE)
        move_idx = validate_pr(base_state, head_state)
    elif args.mode == "play":
        base_state = get_base_state(args.base)
        head_state = load_json("game_state.json", DEFAULT_STATE)
        move_idx = validate_pr(base_state, head_state)
        execute_turn(move_idx, args.player)
    elif args.mode == "render":
        s = load_json("game_state.json", DEFAULT_STATE)
        st = load_json("stats.json", DEFAULT_STATS)
        render_readme(s, st)
