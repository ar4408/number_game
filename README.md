# 数当てゲーム

## 起動方法

Python 3.9以降をインストールしてから、PowerShellでこのフォルダーを開き、次を実行します。

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

ブラウザーで <http://127.0.0.1:5000> を開くと遊べます。終了するときはPowerShellで `Ctrl+C` を押します。

`game.py` はターミナル版、`app.py` はブラウザー版です。ブラウザー版のプレイ記録は、このフォルダーの `game_data.sqlite3` に保存されます。

## 難易度

| 難易度 | 数字の範囲 | 挑戦できる回数 |
| --- | ---: | ---: |
| かんたん | 1〜50 | 10回 |
| ふつう | 1〜100 | 7回 |
| むずかしい | 1〜500 | 9回 |

クリアまたは失敗するとプレイ回数に加算され、クリアした場合は難易度ごとの最少挑戦回数が最高記録として保存されます。
